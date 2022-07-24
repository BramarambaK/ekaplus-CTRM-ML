import spacy
import dateutil.parser as dparser
from dateutil.parser import _timelex, parser
import datetime
import re
import ast
import json
import logging
import requests
from itertools import combinations
from spacy.matcher import Matcher
import get_object_meta
import load_model_and_tag_map


DATE_FORMAT = "%Y-%m-%d"
date_format_dict = {"yyyy-MM-dd":"%Y-%m-%d", "dd-M-yy":"%d-%m-%Y", "dd-mmm-yyy":"%d-%m-%Y", "YYYY-MM-DD":"%Y-%m-%d"}
date_pattern = [{"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}]
name_pattern = [{}]
data_types = ['textbox', 'dropdown', 'datepicker', 'hidden']

get_data_endpoint = "/connect/api/workflow/data"
get_meta_endpoint = "/connect/api/workflow/layout"
security_info_endpoint = "/cac-security/api/userinfo"

# # Header keys
# auth = 'X-Accesstoken'
# tenant = 'X-Tenantid'
# appid = 'appId'
# workflow = 'workFlowTask'
# platform_url_header = 'X-Platformurl'
# device_id = 'Device-Id'
# user_id_ = 'user_id'

# Headers
auth = 'X-AccessToken'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
platform_url_header = 'X-PlatformUrl'
device_id = 'Device-Id'
user_id_ = 'user_id'


p = parser()
info = p.info

def timetoken(token):
    try:
        float(token)
        return True
    except ValueError:
        pass
    return any(f(token) for f in (info.jump,info.weekday,info.month,info.hms,info.ampm,info.pertain,info.utczone,info.tzoffset))

def timesplit(input_string):
    batch = []
    for token in _timelex(input_string):
        # print(f"The token from _timelex is : {token}")
        if timetoken(token):
            if info.jump(token):
                continue
            batch.append(token)
        else:
            if batch:
                yield " ".join(batch)
                batch = []
    if batch:
        yield " ".join(batch)

def replace_dates(doc, dates_dict):
    doc_joined = None
    doc_list = list(doc.split(' '))
    # print(f"The doc list is : {doc_list}")
    doc_list = [token.split('/') if '/' in token else token for token in doc_list]
    doc_list = [token.split('-') if '-' in token else token for token in doc_list]
    left_list = []
    for elem in doc_list:
        if isinstance(elem, list):
            left_list = left_list + elem
        else:
            left_list.append(elem)
    doc_list = left_list
    for date_input, date_parsed in dates_dict.items():
        date_input_list = list(date_input.split(' '))
        # print(f"The date input list is : {date_input_list}")
        length = len(date_input_list)
        if length >= 2:
            str_to_replace = '_ '*length
            str_to_replace = str_to_replace[:-1]
            # print(f"The string to replace is : {str_to_replace}")
            for date_part in date_input_list:
                doc_list = ['_' if date_part in token else token for token in doc_list]
                # print(f"The token list after replacing with _ is : {doc_list}")
                doc_joined = ' '.join(doc_list)
                # print(f"The doc after joining : {doc_joined}")
            doc_joined = doc_joined.replace(str_to_replace, date_parsed)
        # print(f"The document after replacing dates is : {doc_joined}")
    return doc_joined

def transform_sent_dates(doc):
    dates = []

    for item in timesplit(doc):
        try:
            dates.append([item, p.parse(item)])
        except ValueError:
            dates.append([item, None])
    # print(f"The dates are: {dates}")

    if dates is not None:
        dates_dict = {}
        for date in dates:
            # print(f"The date found is : {date}, date format to parse is : {DATE_FORMAT}")
            if date[1] is not None:
                dates_dict[date[0]] = date[1].strftime(DATE_FORMAT)
            # print(f"The parsed date is : {dates_dict[date[0]]}")
            # print(f"The string to replace is : {str(date[0])}")
            # doc = doc.replace(str(date[0]), date[1].strftime(DATE_FORMAT))
        doc_replaced = replace_dates(doc, dates_dict)
        if doc_replaced is None:
            return dates_dict, doc
        else:
            return dates_dict, doc_replaced
    else:
        return None, doc

def get_meta_obj_id(headers_post, input_body):
    """Parse the object meta call."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    platform_url = headers_post[platform_url_header]
    obj_id = headers_post["X-Object"]
    get_meta_url = platform_url + '/connect/api/meta/object/' + str(obj_id)
    logging.info(f"Calling object meta API to get object meta. The URL is: {get_meta_url}")
    if device_id not in headers_post:
        headers_ = {"Authorization":auth_token, "X-TenantID":tenant_id}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {"Authorization":auth_token, "X-TenantID":tenant_id, 'Device-Id':device_id_}
    logging.info("Calling workflow to get object meta.")
    response = requests.get(url=get_meta_url, headers=headers_)
    # logging.info(response)
    if response.status_code == 200:
        json_data = response.json()
        return json_data
    else:
        return None

def partitions(items, k):
    def split(indices):
        i=0
        for j in indices:
            yield items[i:j]
            i = j
        yield items[i:]

    for indices in combinations(range(1, len(items)), k-1):
        yield list(split(indices))

def add_patterns(field, field_description, patterns_map, deleted_tokens):

    all_descriptions = field_description.split(' ')
    n = len(all_descriptions)
    for i in range(1, n+1):
        for x in partitions(all_descriptions, i):
            all_desc = [' '.join(y) for y in x]
            # print(f"All description combinations are: {all_desc}")
            for desc in all_desc:
                if str(desc).lower() not in patterns_map:
                    if str(desc).lower() in deleted_tokens:
                        pass
                    else:
                        patterns_map[str(desc).lower()] = [str(field)]
                else:
                    if len(desc.split(' ')) > 1:
                        patterns_map[str(desc).lower()].append(str(field))
                    else:
                        # deleted_tokens.append(str(desc).lower())
                        # del patterns_map[str(desc).lower()]
                        # pass
                        patterns_map[str(desc).lower()].append(str(field))
    return patterns_map, deleted_tokens

def add_rules_based_on_patterns_map(patterns_map, matcher, date_pattern_):
    if date_pattern_ is True:
        for tokens, fields in patterns_map.items():
            if len(tokens.split(' ')) > 1:
                pattern_list = [{"LOWER":str(token).lower()} for token in tokens.split(' ')]
                for field in fields:
                    matcher.add(str(field), None, pattern_list + [{"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}])
            else:
                for field in fields:
                    matcher.add(str(field), None, [{"LOWER": str(tokens).lower()}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}])
    else:
        for tokens, fields in patterns_map.items():
            if len(tokens.split(' ')) > 1:
                pattern_list = [{"LOWER":str(token).lower()} for token in tokens.split(' ')]
                for field in fields:
                    matcher.add(str(field), None, pattern_list + [{}])
            else:
                for field in fields:
                    matcher.add(str(field), None, [{"LOWER": str(tokens).lower()}, {}])
    return matcher

def create_proxy_labels(nlp, headers_post, input_body):
    noun_forms = ['PROPN', 'NOUN', 'ADJ', 'VERB']
    patterns_map = {}
    patterns_map_date = {}
    deleted_tokens = []
    matcher = Matcher(nlp.vocab)
    object_doc = get_meta_obj_id(headers_post, input_body)
    if 'fields' in object_doc:
        meta_data = object_doc['fields']
        proxy_labels_list = []
        tags = []
        for field, description in meta_data.items():
            proxy_labels_dict = {}
            tags.append(field)
            if 'labelKey' in  description:
                _key = description['labelKey']
                if _key == 'ContractgeneralDetailsOptional' or _key == 'ContractoptionalItemDetails':
                    pass
                else:
                    if _key in description:
                        field_description = description[_key]
                        if field_description is not None:
                            if len(field_description) > 0:
                                proxy_labels_dict[field] = field_description
                                doc = nlp(field_description)
                                for token in doc:
                                    if token.pos_ in noun_forms:
                                        if 'dataType' in description:
                                            proxy_labels_dict['type'] = description['dataType']
                                            if description['dataType'] == 'date':
                                                # print(f"The data type Date for field: {field}")
                                                # print(f"Added rule for the date field : \n {field_description}")
                                                all_descriptions = field_description.split(' ')
                                                matcher.add(str(field), None, [{"LOWER": str(field_description).lower()}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}, {"IS_PUNCT":True}, {"POS":"NUM"}])
                                                patterns_map_date, deleted_tokens = add_patterns(field, field_description, patterns_map_date, deleted_tokens)
                                                if 'format' in description:
                                                    if description['format'] in date_format_dict:
                                                        global DATE_FORMAT
                                                        DATE_FORMAT = date_format_dict[description['format']]
                                                        # print(f"The updated date format is : {DATE_FORMAT}. The date format map is {date_format_dict}")
                                            else:
                                                matcher.add(str(field), None, [{"LOWER": str(field_description).lower()}, {}])
                                                patterns_map, deleted_tokens = add_patterns(field, field_description, patterns_map, deleted_tokens)
                                        else:
                                            # print(f"The data type not found in the description: {description}")
                                            matcher.add(str(field), None, [{"LOWER": str(field_description).lower()}, {}])
                                            patterns_map, deleted_tokens = add_patterns(field, field_description, patterns_map, deleted_tokens)
                                else:
                                    # print(f"Not nouns are: {token}")
                                    # print(token.pos_)
                                    pass
                                proxy_labels_list.append(proxy_labels_dict)
        matcher = add_rules_based_on_patterns_map(patterns_map, matcher, date_pattern_=False)
        matcher = add_rules_based_on_patterns_map(patterns_map_date, matcher, date_pattern_=True)
        # print(f"The rule added to the matcher is  : {patterns_map}")
        # print(f"The deleted tokens are: {deleted_tokens}")
        return matcher, tags, object_doc
    else:
        return None, None, None

def get_matches(nlp, matcher, doc):
    match_dict = {}
    matches = matcher(doc)
    # print(f"The matches are: {matches}")
    span_dict = {}
    span_list = []
    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]  # Get string representation
        span = doc[start:end]  # The matched span
        # print(f"The matcher results: {string_id}, {start}, {end}, {span.text}")
        txt = span.text
        span_list.append(txt)
        if string_id in span_dict:
            span_dict[string_id].append(txt)
        else:
            span_dict[string_id] = [txt]
    return span_dict, span_list

def get_longest_unique_spans(span_list):
    longest_unique_span = []
    span_list_copy = span_list.copy()
    for i in range(len(span_list_copy)):
        if any(span_list_copy[i] in span_list_copy[j] and len(span_list_copy[j]) > len(span_list_copy[i]) for j in range(len(span_list_copy))):
            span_list.remove(span_list_copy[i])
    return span_list

def tag_spans(nlp, matcher, doc):
    span_dict, span_list = get_matches(nlp, matcher, doc)
    longest_unique_span = get_longest_unique_spans(span_list)
    longest_unique_span = list(set(longest_unique_span))
    # print(f"The longest_unique_span is : \n {longest_unique_span}")
    # print(f"The span dict is : {span_dict}")
    match_dict = {}
    for string_id, spans in span_dict.items():
        for span in longest_unique_span:
            if span in spans:
                if len(list(span.split(' '))) >= max([len(list(i.split(' '))) for i in spans]):
                    match_dict[string_id] = span.split(' ')[-1]
                    # print(f"Breaking out of the loop. The span to be tagged is: {span}")
                    break
                else:
                    match_dict[string_id] = span.split(' ')[-1]
    return match_dict


def extend_span(match_dict, text, matcher):
    match_dict_copy = match_dict.copy()
    labels = list(match_dict.keys())
    text_normal = text
    text = text.lower()
    for field, span in match_dict.items():
        pattern_after_span = False
        extended_span = None
        span_normal = span
        span = span.lower()
        span_idx_in_text = text.find(span)
        # print(f"The span is : {span}")
        # print(f"The index of the span is : {span_idx_in_text}")
        right_idx_span = span_idx_in_text + len(span)
        sliced_text = text[right_idx_span:]
        # print(f"The sliced text is : {sliced_text}")
        sliced_text = sliced_text.strip()
        pattern_index_dict = {}
        if len(sliced_text) > 0:
            sliced_text_list = list(sliced_text.split(' '))
            for label in labels:
                if label != field:
                    on_match, patterns = matcher.get(label)
                    if patterns is not None:
                        pattern_tokens = []
                        for pattern_list in patterns:
                            for pattern_dict in pattern_list:
                                if 'LOWER' in pattern_dict:
                                    pattern_tokens.append(pattern_dict['LOWER'])
                        for tokens in pattern_tokens:
                            pattern_idx = text.find(tokens)
                            # print(f"The pattern : {tokens} found at index : {pattern_idx} for the sapn : {span} and the right index of the span is : {right_idx_span}")
                            if pattern_idx != -1:
                                if pattern_idx >= right_idx_span:
                                    if span in pattern_index_dict:
                                        pattern_index_dict[span].append(pattern_idx)
                                    else:
                                        pattern_index_dict[span] = [pattern_idx]
            if span in pattern_index_dict:
                # print(f"The pattern index list for span : {span} is: {pattern_index_dict}")
                closest_pattern_idx = min(pattern_index_dict[span])
                extended_span = span_normal + text_normal[right_idx_span:closest_pattern_idx-1]
                # print(f"The extended span is :{extended_span}")
            else:
                extended_span = span_normal + text_normal[right_idx_span:]
                # print(f"The extended span is :{extended_span}")
            labels_to_update = [key for key, value in match_dict.items() if span_normal == value]
        if extended_span is not None:
            for keys in labels_to_update:
                match_dict_copy[keys] = extended_span
    return match_dict_copy


def generate_tags(match_dict, tags, tag_map):
    match_dict_ = {}
    for tags_, value in match_dict.items():
        for tag in tags:
            if tags_ in tag:
                # print(f"The proxy label is {tags_} and full label is {tag}")
                if tag_map is not None:
                    if tag in tag_map:
                        val_dict = tag_map[tag]
                        if value in val_dict:
                            val_ = val_dict[value]
                            match_dict_[tag] = val_
                        else:
                            match_dict_[tag] = value
                    else:
                        match_dict_[tag] = value
                else:
                    match_dict_[tag] = value
    return match_dict_


def priority_based_on_non_noun_percent(doc, nlp):
    noun_count = 0
    doc_length = 0
    for i in range(len(doc)):
        token = doc[i]
        if token.pos_ != 'NUM':
            if token.pos_ != 'PUNCT':
                doc_length += 1
                if token.pos_ == 'NOUN' or token.pos_ == 'PROPN':
                    noun_count += 1
    noun_pcent = noun_count/doc_length
    if noun_pcent > 0.7 and len(list(doc.noun_chunks)) < 0.20*len(doc):
        return False
    else:
        return True

def strip_non_nouns(doc, nlp):
    doc2 = doc
    for i in range(len(doc)):
        token = doc[i]
        if token.pos_== 'NUM' or token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'PUNCT':
            pass
        else:
            del doc2[i]
    print(f"The second doc is : {doc2}")
    return doc2


def is_nlp_v1_prior(doc, nlp):
    propn_adp = 0
    noun_propn = 0
    noun_noun = 0
    propn_propn = 0
    for i in range(len(doc)):
        token = doc[i]
        if token.pos_ == 'PROPN':
            if i != len(doc) - 1:
                j = i + 1
                token_j = doc[j]
                if token_j.pos_ == 'ADP':
                    propn_adp += 1
                elif token_j.pos_ == 'PROPN':
                    propn_propn += 1
                elif token_j.pos_ == 'NOUN':
                    noun_propn += 1
        elif token.pos_ == 'NOUN':
            if i != len(doc) - 1:
                j = i + 1
                token_j = doc[j]
                if token_j.pos_ == 'PROPN':
                    noun_propn += 1
                elif token_j.pos_ == 'NOUN':
                    noun_noun += 1
        # print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop)
    # print(f"Proper noun - proper noun: {propn_propn}")
    # print(f"Proper noun - ADP : {propn_adp}")
    # print(f"noun - proper noun: {noun_propn}")
    # print(f"noun - noun: {noun_noun}")
    if noun_noun - propn_adp > 0 or propn_propn - propn_adp > 0 or noun_propn - propn_adp > 0:
        return False
    else:
        return True

def tag_text(headers_post, input_body):
    # print("Received request to tag text data.")
    text_data = input_body['sentence']
    # print(f"Text to be tagged is {text_data}.")
    dates_with_source, doc_ = transform_sent_dates(text_data)
    # print(f"The dates with source are : {dates_with_source} and the doc is: \n {doc_}")
    nlp = spacy.load("en_core_web_sm")
    matcher, tags, object_doc = create_proxy_labels(nlp, headers_post, input_body)
    if matcher is None:
        res = {"statusCode": 200, "body":json.dumps({"msg":"Error while parsing object meta."})}
        return res
    else:
        doc = nlp(doc_)
        match_dict = tag_spans(nlp, matcher, doc)
        match_dict_extended = extend_span(match_dict, doc_, matcher)
        # is_v1_prior = is_nlp_v1_prior(doc, nlp)
        is_v1_prior = priority_based_on_non_noun_percent(doc, nlp)
        print(f"Is NLP V1 more prior : {is_v1_prior}")
        model, tag_map = load_model_and_tag_map.load_model_tag_map_file(headers=headers_post)
        # print(f"Loaded up the model and tag mappings. {tag_map}")
        # tag_map = None
        if tag_map is not None:
            tagged_data = generate_tags(match_dict_extended, tags, tag_map)
        else:
            tagged_data = generate_tags(match_dict_extended, tags, tag_map=None)
        # print(f"The tagged text data is :\n {tagged_data}")
        return tagged_data, is_v1_prior, object_doc