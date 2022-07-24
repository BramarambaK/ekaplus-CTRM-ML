# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 18:13:41 2019

@author: amitabh.gunjan
"""
import sys
import os
import time
import requests
from flask import Flask, request
import anomaly_detection
import create_folders
import write_config
import get_data_api

# properties
host_port = os.environ.get('eka_connect_host')

models_and_data_path = '/anomaly-detection/models-and-data'

# URLs and paths
url_auth = host_port + '/property/platform_url'
get_data_url = host_port + "/workflow/data"
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
inp_data = 'data'

# Keys
property_val = 'propertyValue'
saved_data = 'input_df'
saved_model = 'model_path'
config_file = 'conf_file'

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

def validate_token(headers, tenant_id, auth_token, authenticate_url):
    """Validate token Authentication API."""
    headers = {"Content-Type":str(headers['Content-Type']), tenant:tenant_id}
    if authenticate_url is not None:
        authenticate_url = authenticate_url + security_info_endpoint
        response = requests.get(authenticate_url, headers={auth:auth_token})
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

def train_anomaly_model(train_data, conf_contents):
    """Call the function to train the anomaly detection model"""
    anomaly_detection.train_anomaly_detection_model(train_data=train_data, conf_contents=conf_contents)

def check_anomaly(data, conf_contents):
    """Check if the observation is an anomaly."""
    anomalies_ = {"anomalies":anomaly_detection.detect_anomaly(data=data, conf_contents=conf_contents)}
    return anomalies_

def append_anomaly_score_to_data(data, conf_contents):
    """Check if the observation is an anomaly."""
    anomalies_ = {"augmented_data":anomaly_detection.attach_anomaly_scores(data=data, conf_contents=conf_contents)}
    anomalies_['augmented_data'].append({"significant_fields":anomaly_detection.most_variability_fields(conf_contents=conf_contents)})
    return anomalies_

app = Flask(__name__)
@app.route('/train-anomaly-detection-model', methods=['POST'])

def train_():
    """Call the train method for anomaly detection."""
    headers_post = request.headers
    input_body = request.json
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    workflow_task = input_body[workflow]
    method = input_body[get_data_method]
    authenticate_url = get_authentication_url(url_auth, tenant_id)
    if authenticate_url is None:
        return {"message":host_down}
    else:
        response = validate_token(headers=headers_post, tenant_id=tenant_id, auth_token=auth_token, authenticate_url=authenticate_url)
        if response is not None:
            if response.status_code == 200:
                response = response.json()
                user_id = response['id']
                user_id = str(user_id)
                # get the file paths for the model and data.
                conf_contents = create_folders.config_file_contents(models_and_data_path=models_and_data_path, tenant_id=tenant_id, app_id=app_id, user_id=user_id)
                data_frame_path = conf_contents[saved_data]
                # Create folders for the path.
                if os.path.exists(data_frame_path):
                    print("There exists previously trained data for this user.")
                else:
                    write_config.conf_content_writer(models_and_data_path=models_and_data_path, tenant_id=tenant_id, app_id=app_id, user_id=user_id)
                try:
                    if 'data' not in input_body:
                        # The body of the get data API call.
                        print("Fetching the data through workflow data API call.")
                        body_get_data = {appid:app_id, workflow:workflow_task}
                        # Get data for training the model
                        input_data = get_data_api.get_data(get_data_url=get_data_url, headers=headers_post, body=body_get_data, method=method)
                        if input_data is not None:
                            if not input_data:
                                return missing_data_in_request
                            else:

                                input_data_numeric = []
                                for i in input_data:
                                    i = {k:v for k,v in i.items() if type(v) != set}
                                    i = {k:v for k,v in i.items() if type(v) != dict}
                                    i['sentence'] = None
                                    i['sys__createdBy'] = None
                                    i['sys__createdOn'] = None
                                    i['sys__data__state'] = None
                                    i['sys__UUID'] = None
                                    tmp = {k:convert_to_float(v) for k,v in i.items() if k != "userId"}
                                    input_data_numeric.append(tmp)
                                train_anomaly_model(train_data=input_data_numeric, conf_contents=conf_contents)
                                print(trained_model)
                                return trained_model
                        else:
                            return empty_data
                    else:
                        input_data = input_body['data']
                        print("Got data from the request.")
                    if input_data is not None:
                        if not input_data:
                            return missing_data_in_request
                        else:
                            total_training_time = 0
                            tick = time.time()
                            input_data_numeric = []
                            for i in input_data:
                                i = {k:v for k,v in i.items() if type(v) != set}
                                i = {k:v for k,v in i.items() if type(v) != dict}
                                tmp = {k:convert_to_float(v) for k,v in i.items() if k != "userId"}
                                input_data_numeric.append(tmp)
                            train_anomaly_model(train_data=input_data_numeric, conf_contents=conf_contents)
                            total_training_time += time.time() - tick
                            print(trained_model)
                            return trained_model
                    else:
                        return data_fetch_error
                except KeyError:
                    return missing_data_in_request
            else:
                return invalid_auth
        else:
            return invalid_token
    return trained_model

@app.route('/check-anomaly', methods=['POST'])

def check_():
    """Check if a new observation is an anomaly."""
    headers_post = request.headers
    input_body = request.json
    auth_token = headers_post[auth]
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    authenticate_url = get_authentication_url(url_auth, tenant_id)
    if authenticate_url is None:
        return {"message":host_down}
    else:
        response = validate_token(headers=headers_post, tenant_id=tenant_id, auth_token=auth_token, authenticate_url=authenticate_url)
        if response is not None:
            if response.status_code == 200:
                response = response.json()
                user_id = response['id']
                user_id = str(user_id)
                try:
                    input_data = input_body['data']
                    if not input_data:
                        return missing_data_in_request
                    else:
                        if input_data is None:
                            return missing_data_in_request
                        else:
                            conf_contents = create_folders.config_file_contents(models_and_data_path=models_and_data_path, tenant_id=tenant_id, app_id=app_id, user_id=user_id)
                            # Replace string amount with float amount.
                            input_data_numeric = []
                            for i in input_data:
                                i = {k:v for k,v in i.items() if type(v) != set}
                                i = {k:v for k,v in i.items() if type(v) != dict}
                                tmp = {k:convert_to_float(v) for k,v in i.items() if k != "userId"}
                                input_data_numeric.append(tmp)
                            try:
                                anomalies_ = check_anomaly(data=input_data_numeric, conf_contents=conf_contents)
                                data_with_anomaly_score = append_anomaly_score_to_data(data=input_data_numeric, conf_contents=conf_contents)
                                return data_with_anomaly_score
                            except FileNotFoundError:
                                return model_not_trained
                except KeyError:
                    return missing_data_in_request
                    pass
            else:
                msg = invalid_token
                print(msg)
                return msg
        else:
            msg = invalid_token
            return msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5454, debug=False)