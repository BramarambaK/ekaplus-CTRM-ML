import sys
import os
from flask import Flask, request, jsonify
import requests
import train_and_get_recommendation
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
###########
# Constants
###########
# recommendation properties 
port = 8686

# URLs and paths
security_info_endpoint = "/cac-security/api/userinfo"

# Headers
auth = 'Authorization'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
get_data_method = 'method'
obj = 'X-Object'

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


def get_environ_property(env):
    """ Gets the system properties for the specific ENVironment.This will be 
    used for fetching the configurations from mongo and also to save data to mongo."""
    host = os.environ.get(env)
    return host

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


def get_remote_address(request):
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip = {'ip':request.environ['REMOTE_ADDR']}
    else:
        ip = {'ip':request.environ['HTTP_X_FORWARDED_FOR']}
    return ip

def validate_token(headers, tenant_id, auth_token, authenticate_url):
    """Validate token Authentication API."""
    headers = {"Content-Type":str(headers['Content-Type']), tenant:tenant_id}
    if authenticate_url is not None:
        authenticate_url = authenticate_url + security_info_endpoint
        response = requests.get(authenticate_url, headers={auth:auth_token})
    else:
        msg = platform_url_error
        print(msg)
        response = None
        return response
    return response


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

def get_headers_and_data(request):
    headers_post, input_body = request.headers, request.json
    return headers_post, input_body

count_map = {}
def requests_counter(headers_post, input_body):
    response = train_and_get_recommendation.authenticate_and_validate_user(headers_post)
    response = response.json()
    userId = response['id']
    global count_map
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    object_id = headers_post[obj]
    key = str(userId) + str(tenant_id) + str(app_id) + str(object_id)
    if key in count_map:
        count_map[key] += 1
    else:
        count_map[key] = 1
    return count_map, userId

def train_based_on_count(user_id, count_map, headers_post, input_body):
    # if user_id in count_map:
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    object_id = headers_post[obj]
    key = str(user_id) + str(tenant_id) + str(app_id) + str(object_id)
    if count_map[key] > 0:
        msg = train_and_get_recommendation.train(headers_post, input_body)
        count_map[key] = 1
        return msg
    else:
        msg = {"msg":"The count of requests has not reached the threshold. Will not train the model."}
        return msg

app = Flask(__name__)
@app.route("/train-recommendation-api", methods = ['POST'])
def train_():
    """Train recommendation model for an user. Save the model file. 
    Get the predictions for the user. Save the predictions to mongodb."""
    import time
    total_api_time = 0
    tick_ = time.time()
    headers_post, input_body = get_headers_and_data(request)
    try:
        count_map, user_id = requests_counter(headers_post, input_body)
    except:
        logger.error("Invalid request. Please check the request headers.")
        return {"msg":"Invalid request. Please check the request headers."}
    msg = train_based_on_count(user_id, count_map, headers_post, input_body)
    total_api_time += time.time() - tick_
    info_ = 'Time taken to process the request: ' + str(total_api_time)
    logging.info(info_)
    return msg

@app.route("/recommendation", methods = ['POST'])
def recomm():
    import time
    total_api_time = 0
    tick_ = time.time()
    headers_post, input_body = get_headers_and_data(request)
    try:
        response = train_and_get_recommendation.authenticate_and_validate_user(headers_post)
    except:
        logger.error("Invalid request. Please check the request headers.")
        return {"msg":"Invalid request. Please check the request headers."}
    msg = train_and_get_recommendation.recommend(headers_post, input_body, response)
    total_api_time += time.time() - tick_
    info_ = 'Time taken to process the request: ' + str(total_api_time)
    logging.info(info_)
    return msg


@app.route("/train-recommendation-for-all-users", methods=['POST'])
def train_all():
    import time
    total_api_time = 0
    tick_ = time.time()
    headers_post, input_body = get_headers_and_data(request)
    msg = train_and_get_recommendation.train_for_all(headers_post, input_body)
    total_api_time += time.time() - tick_
    info_ = 'Time taken to process the request: ' + str(total_api_time)
    logging.info(info_)
    return msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)