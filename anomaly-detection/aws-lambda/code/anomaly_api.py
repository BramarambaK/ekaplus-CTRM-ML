# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 18:13:41 2019

@author: amitabh.gunjan
"""
import sys
import os
import json
import time
import requests
import logging
import anomaly_detection
import get_data_api
from save_model import save_model_to_s3
import load_model_files

# URLs and paths
security_info_endpoint = "/cac-security/api/userinfo"
data_ext = '/data.dat'
data_ext_cols = '/cols_data.dat'
get_data_endpoint = "/connect/api/workflow/data"
unique_user_endpoint = '/connect/api/workflow/search'

# Headers - to run as lambda.
auth = "X-AccessToken"
tenant = "X-TenantID"
platform_url_ = "X-PlatformUrl"
appid = 'appId'
workflow = 'workFlowTask'
get_data_method = 'method'
obj = 'X-Object'
inp_data = 'data'
device_id = 'Device-Id'

# Errors and messages
platform_url_error = 'Platform URL not found.'
meta_parsing_error = 'Meta parsing error'
data_fetch_error = 'Data could not be fetched.'
invalid_auth = 'Authorization is not valid.'
invalid_token = 'Token validation API returned None.'
recommendation_api_call_invalid = 'API call input is not valid. Please check the headers and body.'
trained_model = 'Successfully trained the model.'
model_not_trained = 'Model has not been trained for the tenant/user.'
dependence_not_found = 'No dependence structure found for the user.'
empty_data = 'Empty array returned in data API call.'
host_down = "Connect host couldn't be reached."
missing_data_in_request = "No data passed in the request to train anomaly model."

def get_environ_property(env):
    """ Gets the system properties for the specific environment. This will be used
    for fetching the configurations from mongo and also to save data to mongo."""
    host = os.environ.get(env)
    return host

def get_authentication_url(url, tenant_id):
    """Get the platform URL for the tenant id by making a property API call."""
    headers = {tenant:str(tenant_id)}
    try:
        response = requests.get(url=url, headers=headers)
        body = response.json()
        try:
            platform_url = body[property_val]
        except KeyError:
            error_type, error_value, error_traceback = sys.exc_info()
            msg = "The key: " + str(error_value) + " was not found in the property API call."
            print(msg)
            platform_url = None
    except (ConnectionRefusedError, requests.exceptions.ConnectionError):
        print(host_down)
        platform_url = None
        return platform_url
    return platform_url

def validate_token(auth_token, platform_url):
    """Validate token Authentication API."""
    if platform_url is not None:
        platform_url = platform_url + security_info_endpoint
        response = requests.get(platform_url, headers={'Authorization':auth_token})
    else:
        response = None
        return response
    return response

def convert_to_float(arg):
    try:
        arg_num = float(arg)
    except (ValueError, TypeError):
        arg_num = arg
    return arg_num

# def train_anomaly_model(train_data, conf_contents):
#     """Call the function to train the anomaly detection model"""
#     anomaly_detection.train_anomaly_detection_model(train_data=train_data, conf_contents=conf_contents)

def train_anomaly_model(train_data):
    """Call the function to train the anomaly detection model"""
    model_objects = anomaly_detection.train_anomaly_detection_model(train_data=train_data)
    return model_objects

# def check_anomaly(data, conf_contents):
#     """Check if the observation is an anomaly."""
#     anomalies_ = {"anomalies":anomaly_detection.detect_anomaly(data=data, conf_contents=conf_contents)}
#     return anomalies_

def check_anomaly(data, model_fit):
    """Check if the observation is an anomaly."""
    anomalies_ = {"anomalies":anomaly_detection.detect_anomaly(data=data, model_fit=model_fit)}
    return anomalies_

# def append_anomaly_score_to_data(data, conf_contents):
#     """Check if the observation is an anomaly."""
#     anomalies_ = {"augmented_data":anomaly_detection.attach_anomaly_scores(data=data, conf_contents=conf_contents)}
#     anomalies_['augmented_data'].append({"significant_fields":anomaly_detection.most_variability_fields(conf_contents=conf_contents)})
#     return anomalies_

def append_anomaly_score_to_data(data, model_fit):
    """Check if the observation is an anomaly."""
    anomalies_ = {"augmented_data":anomaly_detection.attach_anomaly_scores(data=data, model_fit=model_fit)}
    sig_fields = anomaly_detection.most_variability_fields(model_fit=model_fit)
    if sig_fields is not None:
        anomalies_['augmented_data'].append({"significant_fields":sig_fields})
    return anomalies_

def get_training_data(platform_url, app_id, workflow_task, headers_post, method, user_id):
    if user_id is not None:
        filter_data = {}
        field_name_filter = [{"fieldName":"sys__createdBy","value":user_id,"operator":"eq"}]
        filter_data['filter'] = field_name_filter
        body_get_data = {appid:app_id, workflow:workflow_task, "filterData":filter_data}
    else:
        body_get_data = {appid:app_id, workflow:workflow_task}
    get_data_url_ = platform_url + get_data_endpoint
    input_data = get_data_api.get_paginated_data(get_data_url=get_data_url_, headers=headers_post, body=body_get_data, method=method, paginated=True)
    return input_data

def save_model_files(model, headers):
    # save model to output directory
    try:
        logging.info("Calling the save model function.")
        save_model_to_s3(model=model, headers=headers)
    except Exception as e:
        logging.error(e)
        logging.error("Couldn't save model to s3 due to some error.")
    return None

def get_unique_users(platform_url, app_id, auth_token, tenant_id):
    payload_unique_users = {"pointer":[str(app_id)],"qP":{"size":0,"track_total_hits":True,"aggs":{"username":{"terms":{"field":"username.raw","size":10000}}}}}
    headers = {"Authorization":auth_token, "X-TenantID":tenant_id, 'Content-Type':'application/json', 'Cache-Control': 'no-cache'}
    get_unique_users_url = platform_url + unique_user_endpoint
    payload_unique_users = json.dumps(payload_unique_users)
    response = requests.request(method='POST', url=get_unique_users_url, data=payload_unique_users, headers=headers)
    resp = response.json()
    users = resp['data'][0]['username']
    return users


def train_(headers_post, input_body):
    """Call the train method for anomaly detection."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    platform_url = headers_post[platform_url_]
    app_id = input_body[appid]
    workflow_task = input_body[workflow]
    method = input_body[get_data_method]
    object_id = input_body['object']

    print(f"Platform url is {platform_url}")
    response = validate_token(auth_token=auth_token, platform_url=platform_url)
    if response is not None:
        if response.status_code == 200:
            unique_users = get_unique_users(platform_url, app_id, auth_token, tenant_id)
            print(f"Unique users list : {unique_users}")
            if unique_users is not None:
                for user_id in unique_users:
                    try:
                        if 'data' not in input_body:
                            # The body of the get data API call.
                            print("Fetching the data through workflow data API call.")
                            if device_id not in headers_post:
                                headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id}
                            else:
                                device_id_ = headers_post[device_id]
                                headers_to_get_data = {"Authorization":auth_token, "X-TenantID":tenant_id, "X-Object":object_id, 'Device-Id':device_id_}
                            logging.info("Calling the workflow data API to get the training data.")
                            input_data = get_training_data(platform_url, app_id, workflow_task, headers_to_get_data, method, user_id)
                            # import json
                            # with open('D:/work/anomaly-detection/data/data.json', 'w') as f:
                            #     json.dump(input_data, f)
                            if input_data is not None:
                                if not input_data:
                                    return {"statusCode": 200, "body": json.dumps({"message": missing_data_in_request})}
                                else:
                                    input_data_numeric = []
                                    for i in input_data:
                                        i = {k:v for k,v in i.items() if type(v) != set}
                                        i = {k:v for k,v in i.items() if type(v) != dict}
                                        i['sentence'] = None
                                        i['sys__createdOn'] = None
                                        i['sys__data__state'] = None
                                        i['sys__UUID'] = None
                                        if '_id' in i:
                                            del i['_id']
                                        tmp = {k:convert_to_float(v) for k,v in i.items() if k != "sys__createdBy"}
                                        input_data_numeric.append(tmp)
                                    model_objects = train_anomaly_model(train_data=input_data_numeric)
                                    headers_save = {'X-appId':app_id, 'X-Object':object_id, 'X-TenantID':tenant_id, 'userId':user_id}
                                    save_model_files(model_objects, headers_save)
                                    logging.info(trained_model)
                                    print(f"Trained model for user {user_id}")
                            else:
                                print(f"Empty data returned for user {user_id}")

                        else:
                            input_data = input_body['data']
                            logging.info("Got data in the incoming request.")
                            if input_data is not None:
                                if not input_data:
                                    return {"statusCode": 200, "body": json.dumps({"message": missing_data_in_request})}
                                else:
                                    total_training_time = 0
                                    tick = time.time()
                                    input_data_numeric = []
                                    for i in input_data:
                                        i = {k:v for k,v in i.items() if type(v) != set}
                                        i = {k:v for k,v in i.items() if type(v) != dict}
                                        tmp = {k:convert_to_float(v) for k,v in i.items() if k != "sys__createdBy"}
                                        input_data_numeric.append(tmp)
                                    model_objects = train_anomaly_model(train_data=input_data_numeric)
                                    headers_save = {'X-appId':app_id, 'X-Object':object_id, 'X-TenantID':tenant_id}
                                    save_model_files(model_objects, headers_save)
                                    total_training_time += time.time() - tick
                                    logging.info(trained_model)
                                    return {"statusCode": 200, "body": json.dumps({"message": trained_model})}
                            else:
                                return {"statusCode": 200, "body": json.dumps({"message": data_fetch_error})}
                    except KeyError:
                        return {"statusCode": 200, "body": json.dumps({"message": missing_data_in_request})}
            else:
                return {"statusCode": 200, "body": json.dumps({"message": "No users found for the given tenant and app combination."})}
        else:
            return {"statusCode": 200, "body": json.dumps({"message": invalid_token})}
    else:
        return {"statusCode": 200, "body": json.dumps({"message": invalid_token})}
    return {"statusCode": 200, "body": json.dumps({"message": trained_model})}

def check_(headers_post, input_body):
    """Check if a new observation is an anomaly."""
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    platform_url = headers_post[platform_url_]
    object_id = input_body['object']
    heasers_validate = {'Authorization':auth_token, 'X-TenantID':tenant_id}
    response = validate_token(auth_token=auth_token, platform_url=platform_url)
    if response is not None:
        if response.status_code == 200:
            response = response.json()
            user_id = response['userName']
            user_id = str(user_id)
            input_data = input_body['data']
            if not input_data:
                return {"statusCode":200, "body":json.dumps({"message":missing_data_in_request})}
            else:
                if input_data is None:
                    return {"statusCode":200, "body":json.dumps({"message":missing_data_in_request})}
                else:
                    # Replace string amount with float amount.
                    headers_ = {'X-appId':app_id, 'X-TenantID': tenant_id, 'X-Object':object_id, 'userId':user_id}
                    anomaly_model, ecdf, cols_data = load_model_files.load_model_files(headers=headers_)
                    if any([True for i in (anomaly_model, ecdf, cols_data) if i is None]):
                        return {"statusCode":200, "body":json.dumps({"message":"No model trained for this user."})}
                    else:
                        input_data_numeric = []
                        for i in input_data:
                            i = {k:v for k,v in i.items() if type(v) != set}
                            i = {k:v for k,v in i.items() if type(v) != dict}
                            if '_id' in i:
                                del i['_id']
                            tmp = {k:convert_to_float(v) for k,v in i.items() if k != "sys__createdBy"}
                            input_data_numeric.append(tmp)
                        model_fit = {'fit':anomaly_model, 'cols_data':cols_data, 'ecdf':ecdf}
                        anomalies_ = check_anomaly(data=input_data_numeric, model_fit=model_fit)
                        data_with_anomaly_score = append_anomaly_score_to_data(data=input_data_numeric, model_fit=model_fit)
                        return {"statusCode":200, "body":json.dumps(data_with_anomaly_score)}
        else:
            return {"statusCode":200, "body":json.dumps({"message":invalid_token})}
    else:
        return {"statusCode":200, "body":json.dumps({"message":invalid_token})}