import os
import sys
import json
import logging
import traceback
import requests
import get_search_stats
import get_task_stats
import get_workflow_stats
import get_data
import get_apps_list


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# data url
get_data_url = "/connect/api/workflow/search"
method_get_data = 'POST'

# Object
platform_url_error = 'Platform URL not found.'

# URLs and paths
get_data_endpoint = "/connect/api/workflow/data"
get_meta_endpoint = "/connect/api/workflow/layout"
security_info_endpoint = "/cac-security/api/userinfo"
push_data_endpoint = "/connect/api/workflow/userActivity"

# Headers
auth = 'X-AccessToken'
tenant = 'X-TenantID'
appid = 'appId'
workflow = 'workFlowTask'
get_data_method = 'method'
obj_header = 'X-Object'
obj_body = 'object'
platform_url_header = 'X-PlatformUrl'
device_id = 'Device-Id'
user_id_ = 'user_id'


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

def merge_across_and_specific_stats(all_apps_stats, user_specific_stats):
    for i in all_apps_stats:
        user__ = i['user_id']
        for j in user_specific_stats:
            if user__ in j:
                del i['user_id']
                tmp = {}
                tmp['source_app_id'] = 'all_apps'
                tmp['user_activity_data'] = i
                j[user__].append(tmp)
    return user_specific_stats

def merge_all_stats(app_specific_stats):
    all_users_stats = []
    user_specific_stats = []
    app_specific_stats_ = []
    to_delete = ['recentUserAgents', 'recentOSs', 'popularUserAgents', 'popularOSs', 'recentApps', 'popularApps']
    user_stat = {}
    users_list = []
    for k,v in app_specific_stats.items():
        tmp = {}
        if len(v) > 1:
            for tmp_dict in v:
                if len(tmp_dict) > 0:
                    tmp.update(tmp_dict)
                    for i in to_delete:
                        if str(i) in tmp_dict:
                            del tmp_dict[str(i)]
                    tmp_ = {'user_activity_data':tmp_dict}
                    tmp_['source_app_id'] = k
                    user_ = tmp_['user_activity_data']['user_id']
                    del tmp_['user_activity_data']['user_id']
                    app_specific_stats_.append(tmp_)
                    if user_  not in users_list:
                        user_stat[str(user_)] = [tmp_]
                        users_list.append(user_)
                    else:
                        if user_ in user_stat:
                            apps = []
                            for dicts in user_stat[user_]:
                                apps.append(dicts['source_app_id'])
                            if k not in apps:
                                user_stat[str(user_)].append(tmp_)
    user_specific_stats.append(user_stat)
    return user_specific_stats

def post_data(to_post, headers, platform_url):
    """Post data to mongo if data doesn't exist previously."""
    url_post_data = platform_url + push_data_endpoint
    headers['Content-Type'] = 'application/json'
    payload_ = json.dumps(to_post)
    resp = requests.request(method="POST", url=url_post_data, data=payload_, headers=headers)
    if resp.status_code == 200:
        logger.info("Pushed recommendation data to db.")
    else:
        logger.info(resp)
    return None

def create_payload(recommendation_list, across_users_for_apps_, headers_post, platform_url):
    payload = {"UserActivityData":recommendation_list}
    payload_list = []
    for dct in recommendation_list:
        for user_, data in dct.items():
            tmp = {}
            tmp['user_id'] = user_
            tmp['userActivityData'] = data
            payload_list.append(tmp)
    for data in payload_list:
        post_data(data, headers_post, platform_url)
    post_data(across_users_for_apps_, headers_post, platform_url)
    payload_list.append(across_users_for_apps_)
    to_return = {'data':payload_list}
    return to_return

def get_apps_data(app_list, headers_get_data, data_url):
    apps_data = {}
    for app in app_list:
        payload_get_data = {"pointer":[app]}
        app_data = get_data.get_paginated_data(get_data_url=data_url, headers=headers_get_data, body=payload_get_data, method='POST', paginated=True)
        apps_data[app] = app_data
    return apps_data

def get_all_apps_stats(data_dict):
    apps_data = list(data_dict.values())
    # logger.info(f"The train data for all the apps is \n: {apps_data}")
    apps_data = [item for sublist in apps_data for item in sublist]
    all_apps_stats, unique_users = get_workflow_stats.compute(apps_data, across_app_across_user=True, across_user=False)
    return all_apps_stats

def app_user_stat(data_dict):
    app_specific_stats = {}
    for app, app_data in data_dict.items():
        # logger.info(f"The train data for an app is:\n {app_data} \n")
        apps_stats, unique_users = get_workflow_stats.compute(app_data, across_app_across_user=False, across_user=False)
        app_specific_stats[str(app)] = apps_stats
    return app_specific_stats

def across_users_for_app(data_dict):
    across_users_for_apps = []
    across_users_for_apps_ = {}
    for app, app_data in data_dict.items():
        # Across users for an app
        apps_stats_across_users, unique_users = get_workflow_stats.compute(app_data, across_app_across_user=False, across_user=True)
        across_app_act = apps_stats_across_users[0]
        if len(across_app_act) > 0:
            tmp_across_app_act = {'user_activity_data':across_app_act}
            user_id_across_app = across_app_act['user_id']
            del tmp_across_app_act['user_activity_data']['user_id']
            del tmp_across_app_act['user_activity_data']['recentApps']
            del tmp_across_app_act['user_activity_data']['popularApps']
            tmp_across_app_act['source_app_id'] = str(app)
            across_users_for_apps.append(tmp_across_app_act)
    across_users_for_apps_['userActivityData'] = across_users_for_apps
    across_users_for_apps_['user_id'] = 'all_users'
    return across_users_for_apps_

def lambda_handler(event, context):
    logger.info('RECIEVED REQUEST TO TAG SENTENCE')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post = event['headers']
    except:
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
            data_url = headers_post[platform_url_header] + get_data_url
            try:
                app_list = get_apps_list.get_connect_apps(headers_post[platform_url_header], headers_post[tenant], headers_post[auth])
                print(f"The apps list is : \n {app_list}")
            except:
                return {"statusCode": 200,"body": json.dumps({"message": "Error while fetching app UUIDs."})}

            headers_get_data = {'Authorization':headers_post[auth], 'X-TenantID':headers_post[tenant]}
            data_dict = get_apps_data(app_list, headers_get_data, data_url)
            all_apps_stats = get_all_apps_stats(data_dict)
            app_specific_stats = app_user_stat(data_dict)
            across_users_for_apps_ = across_users_for_app(data_dict)
            user_specific_stats = merge_all_stats(app_specific_stats)
            merged_stats = merge_across_and_specific_stats(all_apps_stats, user_specific_stats)
            payload = create_payload(merged_stats, across_users_for_apps_, headers_get_data, headers_post[platform_url_header])
            print(f"The payload is: {payload}")
            return {"statusCode": 200,"body":json.dumps(payload)}
    return {"statusCode": 200,"body": json.dumps({"message": "Platform token is not valid."})}