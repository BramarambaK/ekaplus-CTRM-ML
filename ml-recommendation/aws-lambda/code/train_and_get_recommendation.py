import os
import logging
import json
import sys
import time
import _pickle as cPickle
import traceback
import requests
import numpy as np
import get_data_api
import get_object_meta
import get_recommendations
import push_recommendations
import train_model
import platform    # For getting the operating system name
import subprocess  # For executing a shell command

# properties
recommendation_object = '75e55d43-3a9f-4240-9916-0716e53ee5ec'

# URLs and paths
get_data_endpoint = "/connect/api/workflow/data"
get_meta_endpoint = '/connect/api/meta/object/'
security_info_endpoint = "/cac-security/api/userinfo"
post_recommendation_endpoint = "/connect/api/workflow/recommendation"

# Headers
auth = 'X-AccessToken'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
workflow_for_save = 'workflowTaskForSave'
get_data_method = 'method'
obj_header = 'X-Object'
obj_body = 'object'
platform_url_header = 'X-PlatformUrl'
device_id = 'Device-Id'
user_id_ = 'user_id'

# Headers
# auth = 'X-Accesstoken'
# tenant = 'X-Tenantid'
# appid = 'appId'
# workflow = 'workFlowTask'
# workflow_for_save = 'workflowTaskForSave'
# get_data_method = 'method'
# obj_header = 'X-Object'
# obj_body = 'object'
# platform_url_header = 'X-Platformurl'
# device_id = 'Device-Id'
# user_id_ = 'user_id'
# Keys
meta_key = 'children'
property_val = 'propertyValue'
saved_data = 'input_df'
saved_model = 'model_path'
config_file = 'conf_file'

# Errors and messages 
platform_url_error = 'Platform URL not found.'
meta_parsing_error = 'Meta parsing error'
data_fetch_error = 'Data could not be fetched.'
invalid_auth = 'Platform token is not valid.'
invalid_token = 'Token validation API call failed.'
recommendation_api_call_invalid = 'API call input is not valid. Please check the headers and body.'
trained_model = 'Successfully trained the model.'
model_not_trained = 'Model has not been trained for the tenant/user.'
dependence_not_found = 'No dependence structure found for the user.'
empty_data = 'Empty array returned in data API call.'
host_down = "Connect host couldn't be reached."


def validate_token(headers, authenticate_url):
    """Validate token Authentication API."""
    if authenticate_url is not None:
        logging.info(authenticate_url)
        authenticate_url = authenticate_url + security_info_endpoint
        info_ = "Calling the userInfo API - " + str(authenticate_url)
        logging.info(info_)
        try:
            response = requests.get(authenticate_url, headers=headers)
            return response
        except:
            var = traceback.format_exc()
            print(var)
            logging.error(var)
            return None
    else:
        msg = platform_url_error
        logging.info(msg)
        return None

def authenticate_and_validate_user(headers):
    auth_token = headers[auth]
    authenticate_url = headers[platform_url_header]
    info_ = "Platform URL is : " + str(authenticate_url)
    logging.info(info_)
    if authenticate_url is not None:
        if device_id not in headers:
            headers_ = {'Authorization':auth_token}
        else:
            device_id_ = headers[device_id]
            headers_ = {'Authorization':auth_token, 'Device-Id':device_id_}
        response = validate_token(headers=headers_, authenticate_url=authenticate_url)
        return response


def parse_object_meta(headers_post, input_body):
    """Parse the object meta call."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    obj_id = headers_post[obj_header]
    platform_url = headers_post[platform_url_header]
    get_meta_url = platform_url + get_meta_endpoint + str(obj_id)
    payload = {"appId":input_body[appid], "workFlowTask":input_body[workflow]}
    # headers = {"Authorization":auth_token, "X-TenantID":tenant_id}
    if device_id not in headers_post:
        headers_ = {"Authorization":auth_token, "X-TenantID":tenant_id}
    else:
        device_id_ = headers_post[device_id]
        headers_ = {"Authorization":auth_token, "X-TenantID":tenant_id, 'Device-Id':device_id_}
    logging.info("Calling workflow to get object meta.")
    meta_data = get_object_meta.call_meta_api(get_meta_url, headers_, obj_id, payload)
    print(f"The meta data is : {meta_data}")
    return meta_data

def create_dependence_from_meta(meta_data):
    """Create dependence matrix from the meta data. Do this 
    using the parent child reltionhip from the meta data."""
    logging.info("Parsing dependence structure from object meta.")
    dependence_str_list = []
    try:
        # meta_data = meta_data['objectMeta']['fields']
        meta_data = meta_data['fields']
        for up_keys, values in meta_data.items():
            for keys, val in values.items():
                if keys == "parent" or keys == 'dependsOn' or keys == "recommendation":
                    if len(val) == 1:
                        temp_dict = {}
                        val_0 = val[0]
                        temp_dict[str(up_keys)] = [str(val_0)]
                        dependence_str_list.append(temp_dict)
                    elif len(val) > 1:
                        for k in val:
                            temp_dict = {}
                            temp_dict[str(up_keys)] = [str(k)]
                            dependence_str_list.append(temp_dict)
                elif keys == 'children' or keys == "child_recommendation":
                    if len(val) == 1:
                        temp_dict = {}
                        val_0 = val[0]
                        temp_dict[str(val_0)] = [str(up_keys)]
                        dependence_str_list.append(temp_dict)
                    elif len(val) > 1:
                        for k in val:
                            temp_dict = {}
                            temp_dict[str(k)] = [str(up_keys)]
                            dependence_str_list.append(temp_dict)
                    pass
    except:
        msg = meta_parsing_error
        logging.error(msg)
        return None
    dependence_list = merge_ind_vars_dep_str(dependence_str_list)
    return dependence_list

def merge_ind_vars_dep_str(dependence_str_list):
    vars_ = []
    dep_str_list_new = []
    for dep in dependence_str_list:
        for k,v in dep.items():
            if k not in vars_:
                vars_.append(k)
                dep_str_list_new.append(dep)
            else:
                for dep_ in dep_str_list_new:
                    if k in dep_:
                        dep_[k] = list(set(dep_[k] + v))
    return dep_str_list_new


def unpack_request(headers_post, input_body, user_id):
    """Unpack the request for training and get recommendation."""
    logging.info("Unpacking request.")
    try:
        auth_token = headers_post[auth]
        tenant_id = headers_post[tenant]
        platform_url = headers_post[platform_url_header]
        app_id = input_body[appid]
        workflow_task = input_body[workflow]
        method = input_body[get_data_method]
        object_id = input_body[obj_body]
        if user_id is True:
            user_id = input_body[user_id_]
            return user_id, auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id
        else:
            return auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id
    except:
        msg ="Please check request headers and body."
        logging.info(msg)
        return None

def create_dependence(headers_post, input_body):
    meta_data = parse_object_meta(headers_post, input_body)
    dep = create_dependence_from_meta(meta_data)
    return dep

def get_training_data(platform_url, app_id, workflow_task, headers_post, method, user_id):
    if user_id is not None:
        filter_data = {}
        field_name_filter = [{"fieldName":"sys__createdBy","value":user_id,"operator":"eq"}]
        filter_data['filter'] = field_name_filter
        body_get_data = {appid:app_id, workflow:workflow_task, "filterData":filter_data, "payLoadData":{"fieldName":"sys__createdBy","value":user_id}}
    else:
        body_get_data = {appid:app_id, workflow:workflow_task}
    get_data_url = platform_url + get_data_endpoint
    input_data = get_data_api.get_paginated_data(get_data_url=get_data_url, headers=headers_post, body=body_get_data, method=method, paginated=True)
    return input_data


def call_train_model(input_data, dependence_structure, inner_object, tenant_id, app_id, userId):
    import time
    total_training_time = 0
    tick = time.time()
    model, cols_data, dependence_list_modified, nested_fields_map = train_model.kick_off_training(input_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
    total_training_time += time.time() - tick
    train_time = 'Training time: ' + str(total_training_time)
    logging.info(train_time)
    msg = trained_model
    logging.info(msg)
    return model, cols_data, dependence_list_modified, nested_fields_map

def get_predictions(model, cols_data, dependence_structure, userId, object_id):
    frozen_dep_set = get_recommendations.freeze_dependence_str(dependence_structure)
    input_user_id = {"sys__createdBy": str(userId)}
    recommendations_for_all = []
    result = {}
    recommendation_data = get_recommendations.predict_for_user(input_data=input_user_id, model=model, cols_data=cols_data, dependence_structure=dependence_structure, frozen_dep_set=frozen_dep_set)
    result['recommendation_data'] = recommendation_data
    result['user_id'] = str(userId)
    result['name'] = "ml_recommendation"
    result['source_object_id'] = object_id
    recommendations_for_all.append(result)
    return recommendations_for_all

def get_users_db(headers_get, recommendations_for_all, saved_recommendation_data):
    if len(saved_recommendation_data) == 0:
        new_users = [i['user_id'] for i in recommendations_for_all]
        common_users = []
    else:
        user_ids_db = [i['user_id'] for i in saved_recommendation_data]
        user_ids_computed = [i['user_id'] for i in recommendations_for_all]
        common_users = list(set(user_ids_db) & set(user_ids_computed))
        new_users = list(set(user_ids_computed) - set(user_ids_db))
    return common_users, new_users

# def payload_save_recommendation(recommendation_data, workflow_task_save, app_id):
#     payload = {}
#     output = {}
#     output[workflow_task_save] = recommendation_data
#     payload['task'] = workflow_task_save
#     payload['output'] = output
#     payload['appId'] = app_id
#     payload['workflowTaskName'] = workflow_task_save
#     return payload

def payload_save_recommendation(recommendation_data):
    payload = {}
    payload['data'] = recommendation_data
    return payload

def train(headers_post, input_body):
    try:
        userId, auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id = unpack_request(headers_post, input_body, user_id=True)
    except:
        return {"msg":"Error while parsing input parameters of request."}
    headers_post[obj_header] = object_id
    logging.info("Parsed request parameters.")
    if all(v is not isinstance(v, type(None)) for v in (auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id)):
        response = authenticate_and_validate_user(headers_post)
        if response is not None:
            if response.status_code == 200:
                # response = response.json()
                # userId = response['id']
                # userId = str(userId)
                logging.info("Platform token is valid.")
                dep = create_dependence(headers_post, input_body)
                if dep is not None:
                    dependence_structure = dep
                    inner_object = None
                else:
                    dependence_structure = None
                    inner_object = None
                if device_id not in headers_post:
                    headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id}
                else:
                    device_id_ = headers_post[device_id]
                    headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id, 'Device-Id':device_id_}
                logging.info("Calling the workflow data API to get the training data.")
                input_data = get_training_data(platform_url, app_id, workflow_task, headers_to_get_data, method, userId)
                logging.info(f"Length of the array returned in the data call is {len(input_data)} for user {userId}.")
                if input_data is not None:
                    if not input_data:
                        msg = empty_data
                        logging.info(msg)
                        return {"msg":msg}
                    else:
                        logging.info("Training model for an user.")
                        model, cols_data, dependence_list_modified, nested_fields_map = call_train_model(input_data, dependence_structure, inner_object, tenant_id, app_id, userId)
                        info_ = "Trained model for the given user."
                        logging.info(info_)
                        user_id = [userId]
                        recommendations_for_all = get_recommendations.compute_recommendations(model_list=model, cols_data_list=cols_data, user_ids=user_id, dep_list=dependence_list_modified, object_id=object_id, app_id=app_id, training_data=input_data, nested_fields_map=nested_fields_map, all_users=False) 
                        logging.info("Computing recommendations for the user.")
                        recommendation_payload = payload_save_recommendation(recommendation_data=recommendations_for_all)
                        logging.info("Pushing recommendation data to db.")
                        url_post_data = platform_url + post_recommendation_endpoint
                        push_recommendations.post_data(url_post_data=url_post_data, app_id=app_id, to_post=recommendation_payload, headers=headers_to_get_data)
                        msg = {"message":"Pushed recommendation data to mongodb."}
                        logging.info(f"The recommendation payload: {recommendation_payload}")
                        return msg
                else:
                    msg = data_fetch_error
                    logging.info(msg)
                    return {"msg":msg}
            else:
                msg = invalid_auth
                logging.info(msg)
                return {"msg":msg}
        else:
            msg = invalid_token
            logging.info(msg)
            return {"msg":msg}
    else:
        msg = recommendation_api_call_invalid
        return {"msg":msg}


def train_for_all(headers_post, input_body):
    """Train the recommendation model for all the users. And save the predicted recommendations to db."""
    import time
    total_api_time = 0
    tick_ = time.time()
    try:
        auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id = unpack_request(headers_post, input_body, user_id=False)
    except:
        return {"msg":"Error while parsing input parameters of request."}
    headers_post[obj_header] = object_id
    logging.info("Parsed request parameters.")
    if all(v is not isinstance(v, type(None)) for v in (auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id)):
        response = authenticate_and_validate_user(headers_post)
        if response is not None:
            if response.status_code == 200:
                response = response.json()
                userId = response['id']
                userId = str(userId)
                logging.info("Platform token is valid.")
                # parse meta data for the object and the app and create dependence structure from it.
                meta_data = parse_object_meta(headers_post, input_body)
                dep = create_dependence_from_meta(meta_data)
                if dep is not None:
                    dependence_structure = dep
                    inner_object = None
                else:
                    dependence_structure = None
                    inner_object = None
                # headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id}
                if device_id not in headers_post:
                    headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id}
                else:
                    device_id_ = headers_post[device_id]
                    headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id, 'Device-Id':device_id_}
                logging.info("Calling the workflow data API to get the training data.")
                input_data = get_training_data(platform_url, app_id, workflow_task, headers_to_get_data, method, None)
                if input_data is not None:
                    logging.info("Got the training data for all users.")
                    if not input_data:
                        msg = empty_data
                        logging.info(msg)
                        return {"msg":msg}
                    else:
                        total_training_time = 0
                        tick = time.time()
                        logging.info("Training model for all users.")
                        model_list, cols_data_list, dep_list, user_ids = train_model.train_model_for_all_users(input_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
                        logging.info("Trained model for all users.")
                        total_training_time += time.time() - tick
                        training_time = 'Training time\n', total_training_time
                        logging.info(training_time)
                        logging.info("Training model for system user.")
                        trained_model, cols_data, dependence_list = train_model.train_model_for_system_user(train_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
                        logging.info("Trained model for system user.")
                        model_list.append(trained_model)
                        cols_data_list.append(cols_data)
                        dep_list.append(dependence_list)
                        user_ids.append('system')
                        logging.info("Computing recommendations for users.")
                        result_all_users = get_recommendations.compute_recommendations(model_list=model_list, cols_data_list=cols_data_list, user_ids=user_ids, dep_list=dep_list, object_id=object_id, training_data=input_data, all_users=True)
                        logging.info("Computed recommendations for all users.")
                        recommendation_payload = payload_save_recommendation(recommendation_data=result_all_users)
                        logging.info("Pushing recommendation data to db.")
                        push_recommendations.post_data(platform_url=platform_url, app_id=app_id, recommendation_object=recommendation_object, to_post=recommendation_payload, headers=headers_to_get_data)
                        msg = {"msg":"Executed training for all users."}
                        return msg
                else:
                    msg = data_fetch_error
                    logging.info(msg)
                    return {"msg":msg}
            else:
                msg = invalid_auth
                logging.info(msg)
                return {"msg":msg}
        else:
            msg = invalid_token
            logging.info(msg)
            return {"msg":msg}
    else:
        msg = recommendation_api_call_invalid
        logging.info(msg)
        total_api_time += time.time() - tick_
        api_time = 'Total API time' + str(total_api_time)
        logging.info(api_time)
        return {"msg":msg}
