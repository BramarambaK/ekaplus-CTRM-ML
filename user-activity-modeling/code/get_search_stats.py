import os
import pandas as pd
import numpy as np
import logging
from collections import Counter
import datetime
from time import mktime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# date time format
format_date = "%Y-%m-%d %H:%M:%S"

def get_data_by_user(source_list):
    user_based_data = {}
    for i in source_list:
        user_ = i['userId']
        if user_ in user_based_data:
            user_based_data[user_].append(i)
        else:
            user_based_data[user_] = [i]
    unique_users = list(user_based_data.keys())
    logger.info(f"The users are: {unique_users}")
    return user_based_data, unique_users

def get_search_queries(user_based_data):
    '''
        "requestBody": {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "type": "phrase_prefix",
                        "fields": [
                            "*"
                        ],
                        "query": "crude"
                    }
                }
            ]
        }
    }
    '''
    search_queries = [i['requestBody']['bool']['must'][0]['multi_match']['query'] for user, user_data in user_based_data.items() for i in user_data if 'requestBody' in i]
    # logger.info(f"The search queries across users are: {search_queries}")
    user_based_search = {}
    for user, user_data in user_based_data.items():
        for i in user_data:
            if 'requestBody' in i:
                if user in user_based_search:
                    user_based_search[user].append(i['requestBody']['bool']['must'][0]['multi_match']['query'])
                else:
                    user_based_search[user] = [i['requestBody']['bool']['must'][0]['multi_match']['query']]

    return search_queries, user_based_search

def get_time_indexed_searches_for_users(user_based_data, unique_users):
    user_data_time_indexed = {}
    for user_id in unique_users:
        if user_id in user_based_data:
            _data = [(i['activityDate'], i['requestBody']['bool']['must'][0]['multi_match']['query']) for user, user_data in user_based_data.items() for i in user_data if 'activityDate' in i if 'requestBody' in i]
            user_data_time_indexed[user_id] = _data
        else:
            pass
    logger.info(f"The time indexed user searches are: {user_data_time_indexed}")
    return user_data_time_indexed

def parse_date(date):
    date = date.split('+')[0]
    date = date.split('.')[0]
    date = date.split('T')[0] + ' ' + date.split('T')[1]
    date = datetime.datetime.strptime(date, format_date)
    unix_secs = mktime(date.timetuple())
    return unix_secs

def order_searches_by_time(user_data_time_indexed, unique_users):
    latest_data = {}
    for user in unique_users:
        most_recent_time = 0
        if user in user_data_time_indexed:
            for data_ in user_data_time_indexed[user]:
                date = parse_date(data_[0])
                if date > most_recent_time:
                    most_recent_time = date
                else:
                    pass
            latest_data[user] = data_[1]
    logger.info(f"The latest data is : {latest_data}")
    return latest_data


def get_most_frequent(search_queries):
    data = Counter(search_queries)
    logger.info(f"The most common element is {data.most_common(1)[0][0]}")
    return data.most_common(1)[0][0]

def get_most_popular_search(user_based_data):
    search_queries, search_queries_by_user = get_search_queries(user_based_data)
    most_common = get_most_frequent(search_queries)
    logger.info(f"The searches by users :{search_queries_by_user}")
    most_frequent_searches_by_user = [{k:get_most_frequent(v)} for k,v in search_queries_by_user.items()]
    popular_search = {"system":most_common}
    most_frequent_searches_by_user.append(popular_search)
    logger.info(f"The popular searches before merging are: {most_frequent_searches_by_user}")
    import collections
    super_dict = collections.defaultdict(list)
    for d in most_frequent_searches_by_user:
        for k, v in d.items():
            super_dict[k].append(v)
    return most_frequent_searches_by_user


def get_most_recent_search(user_based_data, unique_users):
    user_data_time_indexed = get_time_indexed_searches_for_users(user_based_data, unique_users)
    recent_searches = order_searches_by_time(user_data_time_indexed, unique_users)
    return recent_searches

def prepare_payload(data, popular_search, recent_searches, input_body):
    '''
        {
            "output": [{
                "user_id": "",
                "source_workflowtaskname": "",
                "user_activity_predictions": {},
                "name": "user_activity_recommendation"
            },
            {
                "user_id": "",
                "source_workflowtaskname": "",
                "user_activity_predictions": {},
                "name": "user_activity_recommendation"
            }]
            "task":"",
            "appId":"",
            "workflowTaskName":""
        }
    '''
    recommendation_list = []
    logger.info(f"The popular search is {popular_search}")
    for i in popular_search:
        for user_id, search in i.items():
            user_acticity_recommendation = {"user_id":user_id, "user_activity_predictions":{"popular":search}, "name":"user_activity_recommendation", "source_workflowtaskname":input_body['workFlowTask']}
            for k,v in recent_searches.items():
                if k in list(user_acticity_recommendation.values()):
                    user_acticity_recommendation['user_activity_predictions']['recent'] = v
        recommendation_list.append(user_acticity_recommendation)
    payload = {"output":{input_body['workFlowTaskForSave']:recommendation_list}}
    payload["appId"] =input_body['appId']
    payload['task'] = input_body['workFlowTaskForSave']
    payload['workflowTaskName'] = input_body['workFlowTaskForSave']
    return payload

def get_search_stats(data, input_body):
    hits_ = data['hits']['hits'] # A list.
    logger.info(hits_)
    source_list = [i['_source'] for i in hits_] # List of dicts
    logger.info(f"Source list {source_list}")
    user_based_data, unique_users = get_data_by_user(source_list)
    popular_search = get_most_popular_search(user_based_data)
    logger.info(f"The popular searches are: {popular_search}")
    recent_searches = get_most_recent_search(user_based_data, unique_users)
    logger.info(f"The recent searches are: {recent_searches}")
    payload = prepare_payload(data, popular_search, recent_searches, input_body)
    return payload


