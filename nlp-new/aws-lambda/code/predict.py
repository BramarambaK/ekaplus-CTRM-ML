import spacy
import logging
import json
import requests
# import load_response_map

'''
tag map example:
    {
		"contractTypeDisplayName": {
			"sell": "Sale",
			"sold": "Sale",
			"buy": "Purchase"
		},
		"productIdDisplayName": {
			"crude": "Crude",
			"cotton": "Cotton",
			"gas oil": "Gasoil",
			"gasoil": "Gasoil"
		}
	}
'''

auth = 'X-AccessToken'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
platform_url_header = 'X-PlatformUrl'
device_id = 'Device-Id'
user_id_ = 'user_id'

def map_prediction_to_dropdown_vals(entities,tag_map):
    if tag_map is not None:
        entities_ = {}
        for k,v in entities.items():
            if k in tag_map:
                if v in tag_map[k]:
                    entities_[k] = tag_map[k][v]
                else:
                    entities_[k] = v
            else:
                entities_[k] = v
        return entities_
    else:
        return entities

def get_prediction(test_data, model, headers, tag_map):
    doc = model(test_data)
    logging.info("Loaded the model to compute prediction.")
    entities__ = [{ent.label_:ent.text} for ent in doc.ents]
    result = {}
    logging.info(entities__)
    for d in entities__:
        result.update(d)
    entities = map_prediction_to_dropdown_vals(result, tag_map)
    return entities

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

def map_text_to_root(headers_post, input_body, entities_):
    if 'obj_meta' in input_body:
        obj_meta = input_body['obj_meta']
    else:
        obj_meta = get_meta_obj_id(headers_post, input_body)
    if obj_meta is not None:
        root_names = {}
        if 'fields' in obj_meta:
            meta_data = obj_meta['fields']
            for field, description_dict in meta_data.items():
                if 'dropdownValue' in description_dict:
                    dd_val = description_dict['dropdownValue']
                    if dd_val in entities_:
                        entities_[field] = entities_[dd_val]
    return entities_