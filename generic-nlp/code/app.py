import sys
import os
import json
import requests
import logging
import traceback
import token_matcher
import call_nlp_v1

logger = logging.getLogger()
logger.setLevel(logging.INFO)
###########
# Constants
###########

# URLs and paths
security_info_endpoint = "/cac-security/api/userinfo"

# Errors and messages 
platform_url_error = 'Platform URL not found.'
invalid_token = 'Token validation API call failed.'
recommendation_api_call_invalid = 'API call input is not valid. Please check the headers and body.'
host_down = "Connect host couldn't be reached."

# URLs and paths
get_data_endpoint = "/connect/api/workflow/data"
get_meta_endpoint = "/connect/api/workflow/layout"
security_info_endpoint = "/cac-security/api/userinfo"

# Headers
auth = 'X-AccessToken'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
platform_url_header = 'X-PlatformUrl'
device_id = 'Device-Id'


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

def get_event_headers_and_payload(event):
    headers_post = event['headers']
    input_body = event['body']
    input_body = input_body.rstrip('\r\n')
    logger.info(input_body)
    input_body = json.loads(input_body)
    headers_post["X-Object"] = input_body["object"]
    headers_post["X-appId"] = input_body["appId"]
    tenant_id = headers_post['X-TenantID']
    return headers_post, input_body

def get_headers_and_data(request):
    headers_post, input_body = dict(request.headers), dict(request.json)
    return headers_post, input_body

def lambda_handler(event, context):
    logger.info('RECIEVED REQUEST TO GET TAGGED TEXT FROM GENERIC NLP')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        logging.info("Please check request headers and body.")
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    try:
        authentication_response = authenticate_and_validate_user(headers_post)
    except:
        logging.info("Error while validating platform token.")
        res = {"statusCode": 200, "body":json.dumps({"msg":"Error while validating platform token."})}
        return res
        
    if authentication_response is not None:
        if authentication_response.status_code == 200:
            logger.info("Platform token is valid.")
            tagged_data, is_v1_prior, obj_meta = token_matcher.tag_text(headers_post, input_body)
            event['obj_meta'] = obj_meta
            tagged_data_v1 = call_nlp_v1.invoke(event)
            logger.info(f"Got the tagged data from process sentence v1 function.")
            if tagged_data_v1 is not None:
                tagged_data_v1_decoded = tagged_data_v1.decode(encoding='UTF-8')
                tagged_data_v1_json = json.loads(tagged_data_v1_decoded)
                if 'body' in tagged_data_v1_json:
                    tagged_data_body_str = tagged_data_v1_json['body']
                    tagged_data_body_json = json.loads(tagged_data_body_str)
                    if 'tags' in tagged_data_body_json:
                        tags_ = tagged_data_body_json['tags']
                        if is_v1_prior is False:
                            tagged_data = {**tags_, **tagged_data}
                        else:
                            tagged_data = {**tagged_data, **tags_}
                        res = {"statusCode": 200, "body":json.dumps({"tags":tagged_data})}
                        return res
                    else:
                        res = {"statusCode": 200, "body":json.dumps({"tags":tagged_data})}
                        return res                     
                else:
                    res = {"statusCode": 200, "body":json.dumps({"tags":tagged_data})}
                    return res
            else:
                res = {"statusCode": 200, "body":json.dumps({"tags":tagged_data})}
                return res
        else:
            res = {"statusCode": 200, "body":json.dumps({"msg":"Platform token is not valid."})}
            return res