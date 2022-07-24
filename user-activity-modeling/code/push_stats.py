import os
import json
import logging
import requests

def push_stats_to_db():
    pass

def post_data(platform_url, app_id, to_post, headers):
	"""Post data to mongo if data doesn't exist previously."""
	url_post_data = platform_url + "/connect/api/workflow"
	headers['Content-Type'] = 'application/json'
	payload_ = str(to_post)
	payload_ = payload_.replace(" ", "")
	payload_ = payload_.replace("'", '"')
	resp = requests.request(method="POST", url=url_post_data, data=payload_, headers=headers)
	if resp.status_code == 200:
		logging.info("Pushed recommendation data to db.")
	else:
		logging.info(resp)
	return None

def put_data(platform_url, app_id, to_put, headers, _id):
	"""Put data to mongo if data exists for the users."""
	url_put_data = platform_url + "/connect/api/workflow" + str(_id)
	to_put = to_put[0]
	resp = requests.request(method="PUT", url=url_put_data, json=to_put, headers=headers)
	if resp.status_code == 200:
		logging.info("Put data to db.")
	else:
		logging.info(resp)
	return None