import os
import logging
import json
import sys
import time
import _pickle as cPickle
import traceback
import requests
from flask import jsonify
import numpy as np
import get_data_api
import get_object_meta
import get_recommendations
import push_recommendations
import train_model

# properties
host_port = os.environ.get('eka_connect_host')
recommendation_object = '75e55d43-3a9f-4240-9916-0716e53ee5ec'

# URLs and paths
auth_endpoint = '/property/platform_url'
get_data_endpoint = "/workflow/data"
get_meta_endpoint = "/meta/object/"
security_info_endpoint = "/cac-security/api/userinfo"
data_ext = '/data.dat'
data_ext_cols = '/cols_data.dat'

# Headers
auth = 'Authorization'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
get_data_method = 'method'
obj = 'X-Object'
connect_host = 'X-ConnectHost'
device_id = 'Device-Id'

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
invalid_auth = 'Authorization is not valid.'
invalid_token = 'Token validation API call failed.'
recommendation_api_call_invalid = 'API call input is not valid. Please check the headers and body.'
trained_model = 'Successfully trained the model.'
model_not_trained = 'Model has not been trained for the tenant/user.'
dependence_not_found = 'No dependence structure found for the user.'
empty_data = 'Empty array returned in data API call.'
host_down = "Connect host couldn't be reached."

def get_authentication_url(url, tenant_id):
    """Get the platform url to be used for token validation."""
    headers = {tenant:str(tenant_id)}
    response = requests.get(url=url, headers=headers)
    body = response.json()
    try:
        platform_url = body[property_val]
    except KeyError:
        error_type, val, tb = sys.exc_info()
        msg = "The key: " + str(val) + " was not found in the property API call."
        print(msg)
        platform_url = None
    return platform_url

def validate_token(headers, authenticate_url):
    """Validate token Authentication API."""
    if authenticate_url is not None:
        authenticate_url = authenticate_url + security_info_endpoint
        response = requests.get(authenticate_url, headers=headers)
    else:
        msg = platform_url_error
        print(msg)
        response = None
        return response
    return response

def authenticate_and_validate_user(headers):
    auth_token = headers[auth]
    tenant_id = headers[tenant]
    url_auth = host_port + auth_endpoint
    authenticate_url = get_authentication_url(url_auth, tenant_id)
    if device_id not in headers:
        headers_ = {'Authorization': auth_token}
    else:
        device_id_ = headers[device_id]
        headers_ = {'Authorization': auth_token, 'Device-Id': device_id_}

    if authenticate_url is not None:
        response = validate_token(headers=headers_, authenticate_url=authenticate_url)
        return response


# def parse_object_meta(auth, tenant, obj):
#     """Parse the object meta call."""
#     meta_data = get_object_meta.call_meta_api(get_meta_url, auth, tenant, obj)
#     return meta_data

def parse_object_meta(headers_post):
    """Parse the object meta call."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    obj_id = headers_post[obj]
    # host_port = headers_post[connect_host]
    get_meta_url = host_port + get_meta_endpoint
    meta_data = get_object_meta.call_meta_api(get_meta_url, auth_token, tenant_id, obj_id)
    return meta_data

def create_dependence_from_meta(meta_data):
    """Create dependence matrix from the meta data. Do this 
    using the parent child reltionhip from the meta data."""
    dependence_str_list = []
    try:
        meta_data = meta_data['fields']
        for up_keys, values  in meta_data.items():
            for keys, val in values.items():
                if keys == meta_key:
                    if len(val) == 1:
                        val_0 = val[0]
                        temp_dict = {}
                        temp_dict[str(val_0)] = [str(up_keys)] 
                        dependence_str_list.append(temp_dict)
                    elif len(val) > 1:
                        for k in val:
                            temp_dict = {}
                            temp_dict[str(k)] = [str(up_keys)] 
                            dependence_str_list.append(temp_dict)
                else:
                    pass
    except:
        msg = meta_parsing_error
        print(msg)
        return None
    return dependence_str_list

def unpack_request(headers_post, input_body):
    """Unpack the request for training and get recommendation."""
    try:
        auth_token = headers_post[auth]
        tenant_id = headers_post[tenant]
        app_id = input_body[appid]
        workflow_task = input_body[workflow]
        method = input_body[get_data_method]
        object_id = headers_post[obj]
    except:
        msg ="Please check request headers and body."
        print(msg)
    return auth_token, tenant_id, app_id, workflow_task, method, object_id

def create_dependence(headers_post):
    meta_data = parse_object_meta(headers_post)
    dep = create_dependence_from_meta(meta_data)
    return dep

def get_training_data(app_id, workflow_task, headers_post, method):
    body_get_data = {appid:app_id, workflow:workflow_task}
    get_data_url = host_port + get_data_endpoint
    # input_data = get_data_api.get_data(get_data_url=get_data_url, headers=headers_post, body=body_get_data, method=method)
    input_data = get_data_api.get_paginated_data(get_data_url=get_data_url, headers=headers_post, body=body_get_data, method=method, paginated=False)
    return input_data

def call_train_model(input_data, dependence_structure, inner_object, tenant_id, app_id, userId):
    import time
    total_training_time = 0
    tick = time.time()
    model, cols_data, dependence_list_modified = train_model.kick_off_training(input_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
    total_training_time += time.time() - tick
    train_time = 'Training time: ' + str(total_training_time)
    logging.info(train_time)
    msg = trained_model
    return model, cols_data, dependence_list_modified

def get_predictions(model, cols_data, dependence_structure, userId, object_id):
    frozen_dep_set = get_recommendations.freeze_dependence_str(dependence_structure)
    input_user_id = {"userId": str(userId)}
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

def push_recommendations_to_db(common_users, new_users, host_port, app_id, recommendation_object, saved_recommendation_data, recommendations_for_all, headers_post):
    if not common_users:
        logging.info("Common users list is empty.")
        push_recommendations.post_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_post=recommendations_for_all, headers=headers_post)
    else:
        for user in common_users:
            user_recommendation = [i for i in recommendations_for_all if i['user_id'] == user]
            _id_in_data = [i['_id'] for i in saved_recommendation_data if i['user_id'] == user]
            for i in _id_in_data:
                push_recommendations.put_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_put=user_recommendation, headers=headers_post, _id=i)
        if not new_users:
            pass
        else:
            for user in new_users:
                user_recommendation = [i for i in recommendations_for_all if i['user_id'] == user]
                push_recommendations.post_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_post=user_recommendation, headers=headers_post)

def pull_recommendations(headers_post, app_id, recommendation_object, userId, sys_user=False):
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    object_id = headers_post['X-ObjectName']

    if sys_user == False:
        get_data_url = host_port + "/data/" + app_id + "/" + recommendation_object + "?user_id=" + str(userId) + "&" + "source_object_id=" + str(object_id)
    else:
        get_data_url = host_port + "/data/" + app_id + "/" + recommendation_object + "?user_id=" + 'system' +  "&" + "source_object_id=" + str(object_id)
    headers_get = {"Authorization":auth_token, "X-TenantID":tenant_id}
    recommendation_data = requests.request(method='GET', url=get_data_url, headers=headers_get)
    recommendation_data = recommendation_data.json()
    if len(recommendation_data) > 0:
        for data in recommendation_data:
            try:
                if data['source_object_id'] == object_id:
                    logging.info("Found object recommendation data.")
                    recommendation_data = data['recommendation_data']
                    recommendation_data = jsonify(recommendation_data)
                    return recommendation_data
                else:
                    pass
            except KeyError as e:
                info_ = "The key"+ str(e) + " was not found in the recommendation data."
                logging.error(info_)
                pass
    else:
        return None

def train(headers_post, input_body):
    auth_token, tenant_id, app_id, workflow_task, method, object_id = unpack_request(headers_post, input_body)
    if all(v is not isinstance(v, type(None)) for v in (auth_token, tenant_id, app_id, workflow_task, method)):
        response = authenticate_and_validate_user(headers_post)
        if response is not None:
            if response.status_code == 200:
                response = response.json()
                userId = response['id']
                userId = str(userId)
                logging.info("Authorization is valid.")
                dep = create_dependence(headers_post)
                if dep is not None:
                    dependence_structure = dep
                    inner_object = None
                else:
                    dependence_structure = None
                    inner_object = None
                headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id, "X-ConnectHost":host_port}
                logging.info("Calling the workflow data API to get the training data.")
                input_data = get_training_data(app_id, workflow_task, headers_to_get_data, method)
                if input_data is not None:
                    if not input_data:
                        msg = empty_data
                        print(msg)
                        return(msg)
                    else:
                        model, cols_data, dependence_list_modified = call_train_model(input_data, dependence_structure, inner_object, tenant_id, app_id, userId)
                        info_ = "Trained model for the given user."
                        logging.info(info_)
                        recommendations_for_all = get_predictions(model=model, cols_data=cols_data, dependence_structure=dependence_list_modified, userId=userId, object_id=object_id)
                        logging.info("Computed predictions.")
                        get_data_url = host_port + "/data/" + app_id + "/" + recommendation_object
                        headers_get = {"Authorization":auth_token, "X-TenantID":tenant_id}
                        saved_recommendation_data = requests.request(method='GET', url=get_data_url, headers=headers_get)
                        saved_recommendation_data = saved_recommendation_data.json()
                        logging.info("Fetched the recommendation data from db.")
                        app_object_recommendation_data = []
                        for i in saved_recommendation_data:
                            try:
                                if i['source_object_id'] == object_id:
                                    app_object_recommendation_data.append(i)
                                else:
                                    pass
                            except:
                                pass
                        common_users, new_users = get_users_db(headers_get, recommendations_for_all, app_object_recommendation_data)
                        headers_post_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id}
                        push_recommendations_to_db(common_users, new_users, host_port, app_id, recommendation_object, app_object_recommendation_data, recommendations_for_all, headers_post_data)
                        logging.info("Pushed recommendation data to db.")
                        msg = {"msg":"Pushed recommendation data to mongo."}
                        return msg
                else:
                    msg = data_fetch_error
                    print(msg)
                    return msg
            else:
                msg = invalid_auth
                print(msg)
                return msg
        else:
            msg = invalid_token
            print(msg)
            return msg
    else:
        msg = recommendation_api_call_invalid
        return msg


def recommend(headers_post, input_body, authentication_response):
    """Get recommendation using the saved recommendation model. Retrieve the recommendations
    from mongodb when it is called for."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    if all(v is not None for v in (auth_token, tenant_id, app_id)):
        if authentication_response is not None:
            if authentication_response.status_code == 200:
                authentication_response = authentication_response.json()
                userId = authentication_response['id']
                userId = str(userId)
                recommendation_data = pull_recommendations(headers_post, app_id, recommendation_object, userId, False)
                if recommendation_data is None:
                    recommendation_data = pull_recommendations(headers_post, app_id, recommendation_object, userId, True)
                    if recommendation_data is None:
                        return {"msg":"Do not have recommendation data for the requested object."}
                    else:
                        logging.info("Pulled recommendations from db for system user.")
                        return recommendation_data
                else:
                    logging.info("Pulled recommendations from db.")
                    return recommendation_data
            else:
                msg = invalid_auth
                print(msg)
                return msg
        else:
            msg = invalid_token
            return msg
    else:
        msg = recommendation_api_call_invalid
        print(msg)
        return msg


def train_for_all(headers_post, input_body):
    """Train the recommendation model for all the users. And save the predicted recommendations to db."""
    auth_token, tenant_id, app_id, workflow_task, method, object_id = unpack_request(headers_post, input_body)
    if all(v is not isinstance(v, type(None)) for v in (auth_token, tenant_id, app_id, workflow_task, method)):
        response = authenticate_and_validate_user(headers_post)
        if response is not None:
            if response.status_code == 200:
                response = response.json()
                userId = response['id']
                userId = str(userId)
                logging.info("Authorization is valid.")
                # parse meta data for the object and the app and create dependence structure from it.
                meta_data = parse_object_meta(headers_post)
                dep = create_dependence_from_meta(meta_data)
                if dep is not None:
                    dependence_structure = dep
                    inner_object = None
                else:
                    dependence_structure = None
                    inner_object = None
                body_get_data = {appid:app_id, workflow:workflow_task}
                # Get data for training the model
                get_data_url = host_port + "/workflow/data"
                logging.info("Calling the get data workflow for getting all the data.")
                input_data = get_data_api.get_paginated_data(get_data_url=get_data_url, headers=headers_post, body=body_get_data, method=method, paginated=False)
                if input_data is not None:
                    if not input_data:
                        msg = empty_data
                        print(msg)
                        return(msg)
                    else:
                        import time
                        total_training_time = 0
                        tick = time.time()
                        logging.info("Training model for all users.")
                        model_list, cols_data_list, dep_list, user_ids = train_model.train_model_for_all_users(input_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
                        total_training_time += time.time() - tick
                        training_time = 'Training time\n', total_training_time
                        logging.info(training_time)
                        trained_model, cols_data, dependence_list = train_model.train_model_for_system_user(input_data=input_data, dependence_list=dependence_structure, inner_object=inner_object)
                        logging.info("Trained model for all users.")
                        model_list.append(trained_model)
                        cols_data_list.append(cols_data)
                        dep_list.append(dependence_list)
                        user_ids.append('system')
                        result_all_users = get_recommendations.compute_recommendations(model_list=model_list, cols_data_list=cols_data_list, user_ids=user_ids, dep_list=dep_list, object_id=object_id) 
                        logging.info("Computed predictions for all users.")
                        # print("computed recommendations\n", result_all_users)
                        get_data_url = host_port + "/data/" + app_id + "/" + recommendation_object
                        headers_get = {"Authorization":auth_token, "X-TenantID":tenant_id}
                        recommendation_data = requests.request(method='GET', url=get_data_url, headers=headers_get)
                        recommendation_data = recommendation_data.json()
                        logging.info("Fetched the recommendation data from db.")
                        app_object_recommendation_data = []
                        for i in recommendation_data:
                            try:
                                if i['source_object_id'] == object_id:
                                    app_object_recommendation_data.append(i)
                                else:
                                    pass
                            except:
                                pass
                        common_users, new_users = get_users_db(headers_get, result_all_users, app_object_recommendation_data)
                        if not common_users:
                            push_recommendations.post_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_post=result_all_users, headers=headers_post)
                        else:
                            for user in common_users:
                                user_recommendation = [i for i in result_all_users if i['user_id'] == user]
                                _id_in_data = [i['_id'] for i in app_object_recommendation_data if i['user_id'] == user]
                                for i in _id_in_data:
                                    push_recommendations.put_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_put=user_recommendation, headers=headers_post, _id=i)
                            if not new_users:
                                pass
                            else:
                                for user in new_users:
                                    user_recommendation = [i for i in result_all_users if i['user_id'] == user]
                                    push_recommendations.post_data(host_port=host_port, app_id=app_id, recommendation_object=recommendation_object, to_post=user_recommendation, headers=headers_post)
                        result_all_users = jsonify(result_all_users)
                        logging.info("Pushed recommendation data to db.")
                        msg = {"message":"Pushed recommendation data to mongodb."}
                        return msg
                else:
                    msg = data_fetch_error
                    print(msg)
                    return msg
            else:
                msg = invalid_auth
                print(msg)
                return msg
        else:
            msg = invalid_token
            print(msg)
            return msg
    else:
        msg = recommendation_api_call_invalid
        print(msg)
        return msg