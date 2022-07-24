import json
import requests
import os
import sys
import boto3
import time
import train_and_get_recommendation
import get_apps_list
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Headers
appid = 'appId'
obj_body = 'object'
auth = 'X-AccessToken'
tenant = 'X-TenantID'
platform_url_header = 'X-PlatformUrl'

# Lambda specific resource IDs
logical_resource_id = 'TrainRecommendationForAnUserFunction'
logical_resource_id_train_all = 'TrainRecommendationForAllUsersFunction'
stack_name = os.environ.get('STACK_NAME')

# Connect Endpoints
unique_user_endpoint = '/connect/api/workflow/search'
train_wflow_endpoint = '/connect/api/workflow/recommendation/trainingData'

# Messages
invalid_auth = 'Platform token is not valid.'
validation_api_failed = 'Token validation API call failed.'
users_list_not_found = {"statusCode": 200,"body": json.dumps({"message":"Couldn't fetch the unique users list."})}
invoked_training_for_user = {"statusCode": 200,"body": json.dumps({"message":"Invoked the lambda function to train for an user."})}
check_request = {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
invoked_training_for_tenant = {"statusCode": 200,"body": json.dumps({"message":"Invoked the train recommendation lambda function for given tenant."})}

def get_event_headers_and_payload(event):
    headers_post = event['headers']
    input_body = event['body']
    input_body = json.loads(input_body)
    return headers_post, input_body

count_map = {}
def requests_counter(headers_post, input_body):
    logging.info("Counting the number of request by the particular user.")
    response = train_and_get_recommendation.authenticate_and_validate_user(headers_post)
    if response is not None:
        response = response.json()
        userId = response['id']
        global count_map
        tenant_id = headers_post[tenant]
        app_id = input_body[appid]
        object_id = input_body[obj_body]
        key = str(userId) + str(tenant_id) + str(app_id) + str(object_id)
        if key in count_map:
            count_map[key] += 1
        else:
            count_map[key] = 1
        return count_map, userId
    else:
        logging.error("Error while calling connect/platform APIs")
        pass

def train_based_on_count(user_id, count_map, headers_post, input_body):
    tenant_id = headers_post[tenant]
    app_id = input_body[appid]
    object_id = input_body[obj_body]
    key = str(user_id) + str(tenant_id) + str(app_id) + str(object_id)
    if count_map[key] > 0:
        msg = train_and_get_recommendation.train(headers_post, input_body)
        count_map[key] = 1
        return msg
    else:
        msg = {"msg":"The count of requests has not reached the threshold. Will not train the model."}
        return msg

def recomm(event, context):
    logger.info('RECIEVED REQUEST TO GET RECOMMENDATION')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        return check_request
    import time
    total_api_time = 0
    tick_ = time.time()
    authentication_response = train_and_get_recommendation.authenticate_and_validate_user(headers_post)
    msg = train_and_get_recommendation.recommend(headers_post, input_body, authentication_response)
    total_api_time += time.time() - tick_
    logger.info(f'Total API time : {total_api_time}')
    res = {"statusCode": 200, "body":json.dumps({"message":msg})}
    return res

def get_user_ids(headers_post, input_body):
    try:
        auth_token, tenant_id, platform_url, app_id, workflow_task, method, object_id = train_and_get_recommendation.unpack_request(headers_post, input_body, False)
    except:
        logger.info("Error while parsing input parameters of request.")
        return None

    payload_unique_users = {"pointer":[str(app_id)],"qP":{"size":0,"track_total_hits":True,"aggs":{"username":{"terms":{"field":"username.raw","size":10000}}}}}
    headers = {"Authorization":auth_token, "X-TenantID":tenant_id, 'Content-Type':'application/json', 'Cache-Control': 'no-cache'}
    get_unique_users_url = platform_url + unique_user_endpoint
    payload_unique_users = json.dumps(payload_unique_users)
    response = requests.request(method='POST', url=get_unique_users_url, data=payload_unique_users, headers=headers)
    if response.status_code == 200:
        resp = response.json()
        user_ids = resp['data'][0]['username']
        logger.info(f"The user Ids are: {user_ids}")
        users = {'user_ids':user_ids}
        return users
    else:
        logger.info(f"The status code: {response.status_code}")
        logger.info(f"The connect endpoint: {get_unique_users_url}, didn't return users list.")
        return None


def get_physical_resource(logical_resource_id, stack_name):
    cfn_client = boto3.client('cloudformation')
    logger.info("Call to get the stack resources:")
    response = cfn_client.describe_stack_resources(StackName=stack_name, LogicalResourceId=logical_resource_id)
    logger.info("The stack resource to be invoked is:")
    logger.info(response)
    for i in response['StackResources']:
        if i['LogicalResourceId'] == logical_resource_id:
            physical_resource_id = i['PhysicalResourceId']
        else:
            logger.info("The stack does not have the child lambda function.")
            physical_resource_id = logical_resource_id
    logger.info(f"The physical resource id of the function to be invoked is : {physical_resource_id}")
    return physical_resource_id

def invoke_child_lambda(users, physical_resource_id, headers_post, input_body):
    lambda_client = boto3.client('lambda')
    logger.info("Created the lambda client.")
    users = users['user_ids']
    logger.info(f"The users found in the data {users}.")
    for i in users:
        input_body['user_id'] = i
        payload = {"headers":headers_post, "body":input_body}
        logger.info(f"Invoking the lambda function with the payload: {payload}.")
        resp = lambda_client.invoke(FunctionName=physical_resource_id, InvocationType='Event', Payload=json.dumps(payload))
        logger.info(f"response:{resp}")
    return None

def get_app_ids(headers_post):
    try:
        app_list = get_apps_list.get_connect_apps(headers_post[platform_url_header], headers_post[tenant], headers_post[auth])
        print(f"The apps list is : \n {app_list}")
        return app_list
    except:
        return None

def get_train_wflows(headers_post, train_wflow_url, app):
    payload = json.dumps({"source_app_id":str(app)})
    if 'Content-Type' in headers_post:
        del headers_post['Content-Type']
    res = requests.get(url=train_wflow_url, data=payload, headers=headers_post)
    if res.status_code == 200:
        return res.json()
    else:
        return None

def prepare_event_obj(wflow, headers_post):
    task = wflow['taskId']
    object_id = wflow['object']
    app_id = wflow['refTypeId']
    payload = {"appId":app_id, "method":"POST", "workFlowTask":task,"object":object_id}
    payload = json.dumps(payload)
    event = {'body':payload, 'headers':headers_post}
    return event

def invoke_train_all_lambda(physical_resource_id, payload):
    lambda_client = boto3.client('lambda')
    logger.info("Created the lambda client.")
    logger.info(f"Invoking the train all lambda function with the payload: {payload}.")
    resp = lambda_client.invoke(FunctionName=physical_resource_id, InvocationType='Event', Payload=json.dumps(payload))
    logger.info(f"response:{resp}")
    return None

def train_one(event, context):
    """Train recommendation model for an user. Save the model file. 
    Get the predictions for the user. Save the predictions to mongodb."""

    logger.info('RECIEVED REQUEST TO TRAIN RECOMMENDATION FOR AN USER')
    logger.info('EVENT OBJECT')
    logger.info(event)
    # logger.info(context)
    try:
        headers_post, input_body = event['headers'], event['body']
        logger.info(f"Got the headers and the body of the request: Headers :{headers_post}, Body: {input_body}")
    except:
        logging.info("Please check request headers and body.")
        res = {"statusCode": 200,"body": json.dumps({"msg": "Please check the request headers and body."})}
        return res
    total_api_time = 0
    tick_ = time.time()
    logging.info("Training recommendation model for an user now.")
    msg = train_and_get_recommendation.train(headers_post, input_body)
    total_api_time += time.time() - tick_
    logger.info(f'API time : {total_api_time}')
    res = {"statusCode": 200,"body": json.dumps({"msg": msg})}
    return res


def train_all(event, context):
    logger.info('RECIEVED REQUEST TO TRAIN RECOMMENDATION FOR ALL USERS/OBJECT/APP')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        logging.info("Please check request headers and body.")
        return check_request
    import time
    total_api_time = 0
    tick_ = time.time()
    total_api_time += time.time() - tick_
    logging.info("Getting the users list.")
    users = get_user_ids(headers_post, input_body)
    if users is not None:
        if 'user_ids' in users:
            if len(users['user_ids']) > 0:
                logging.info("Training the model for all users now.")
                physical_resource_id = get_physical_resource(logical_resource_id, stack_name)
                invoke_child_lambda(users, physical_resource_id, headers_post, input_body)
                total_api_time += time.time() - tick_
                logger.info(f'Total API time : {total_api_time}')
                msg = invoked_training_for_user
            else:
                msg = users_list_not_found
        else:
            msg = users_list_not_found
    else:
        msg = users_list_not_found
    return msg

def call_train_all(event, context):
    logger.info('RECIEVED REQUEST TO TRAIN RECOMMENDATION FOR ALL APP/OBJECT/USER COMBINATION FOR A TENANT')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post = event['headers']
    except:
        logging.info("Please check request headers and body.")
        return check_request
    response = train_and_get_recommendation.authenticate_and_validate_user(headers_post)
    if response is not None:
        if response.status_code == 200:
            logging.info("Getting appIds for all tenants.")
            app_ids = get_app_ids(headers_post)
            logging.info(f"The appIds are: {app_ids}")
            if app_ids is None:
                msg = {"statusCode": 200,"body": json.dumps({"message":"Couldn't fetch the appIds."})}
                logging.info("Couldn't fetch the appIds.")
                return msg
            else:
                platform_url = headers_post[platform_url_header] # Must Ask Jay to use this header for sending platform url.
                train_wflow_url = platform_url + train_wflow_endpoint
                logger.info(f"The URL to get the workflows: {train_wflow_url}")
                headers_get_wflows = {"Authorization":headers_post[auth], "X-TenantID":headers_post[tenant]}
                for app in app_ids:
                    train_wflows = get_train_wflows(headers_get_wflows, train_wflow_url, app)
                    logging.info(f"The train workflows are : {train_wflows}")
                    if len(train_wflows) > 0:
                        for wflow in train_wflows:
                            event = prepare_event_obj(wflow, headers_post) # Add workflowtask, appId, object and method='POST'
                            logging.info(f"The event object is : {event}")
                            physical_resource_id = get_physical_resource(logical_resource_id_train_all, stack_name)
                            invoke_train_all_lambda(physical_resource_id, event)
                            logger.info(f"Invoked the lambda function to train for app: {app} and for workflow: {wflow}.")
            return invoked_training_for_tenant
        else:
            logging.info(invalid_auth)
            return {"statusCode": 200,"body": json.dumps({"message":invalid_auth})}
    else:
        logging.info(validation_api_failed)
        return {"statusCode": 200,"body": json.dumps({"message":validation_api_failed})}