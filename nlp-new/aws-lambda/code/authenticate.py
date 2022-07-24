import logging
import requests
import traceback

# Headers
auth = 'X-AccessToken'
obj = 'X-Object'
appid = 'X-appId'
obj = 'X-Object'
platform_url = 'X-PlatformUrl'
device_id = 'Device-Id'

# URLs and paths
security_info_endpoint = "/cac-security/api/userinfo"

def validate_token(headers, authenticate_url):
    """Validate token Authentication API."""
    logging.info(authenticate_url)
    authenticate_url = authenticate_url + security_info_endpoint
    info_ = "Calling the userInfo API - " + str(authenticate_url)
    logging.info(info_)
    try:
        response = requests.get(authenticate_url, headers=headers)
        return response
    except:
        var = traceback.format_exc()
        logging.error(var)
        return None

def authenticate_and_validate_user(headers):
    auth_token = headers[auth]
    authenticate_url = headers[platform_url]
    if device_id not in headers:
        headers_ = {'Authorization': auth_token}
    else:
        device_id_ = headers[device_id]
        headers_ = {'Authorization': auth_token, 'Device-Id': device_id_}
    info_ = "Platform URL is : " + str(authenticate_url)
    logging.info(info_)
    if authenticate_url is not None:
        response = validate_token(headers=headers_, authenticate_url=authenticate_url)
        return response