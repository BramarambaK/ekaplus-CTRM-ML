import json
import requests

meta_endpoint = '/connect/api/meta/app'
apps_endpoint = '/spring/apps?_dc=1589541458058&apptype=Pre-packaged%20Apps&isAdminContext=&includeSeededApps=true'

def get_apps(url, tenant, auth):
    headers = {'Authorization':auth, 'X-TenantID':tenant}
    url_ = url + apps_endpoint
    res = requests.request(method='GET', url=url_, headers=headers)
    if res.status_code == 200:
        json_ = res.json()
        return json_
    else:
        return None

def get_meta_connect_apps(url, tenant, auth):
    headers = {'Authorization':auth, 'X-TenantID':tenant}
    url_ = url + meta_endpoint
    res = requests.request(method='GET', url=url_, headers=headers)
    if res.status_code == 200:
        json_ = res.json()
        return json_
    else:
        return None

def get_connect_apps(url, tenant, auth):
    app_json = get_apps(url, tenant, auth)
    app_meta_json = get_meta_connect_apps(url, tenant, auth)
    if app_json and app_meta_json:
        _id_apps = [i['_id'] for i in app_json]
        app_ids = [i['sys__UUID'] for i in app_meta_json  if 'platform_id' in i if i['platform_id'] in _id_apps]
    else:
        app_ids = None
    return app_ids