# -*- coding: utf-8 -*-
"""
Created on 11 March 2020

@author: amitabh.gunjan

API for pushing predicted recommendation data to mongoDB and for fetching the same."""

import requests
import os
import logging
import json
import sys
import numpy as np

def post_data(url_post_data, app_id, to_post, headers):
	"""Post data to mongo if data doesn't exist previously."""
	headers['Content-Type'] = 'application/json'
	payload_ = json.dumps(to_post)
	resp = requests.request(method="POST", url=url_post_data, data=payload_, headers=headers)
	if resp.status_code == 200:
		logging.info("Pushed recommendation data to db. Status Code: 200")
	else:
		logging.info(resp)
	return None

def put_data(platform_url, app_id, recommendation_object , to_put, headers, _id):
	"""Put data to mongo if data exists for the users."""
	url_put_data = platform_url + "/connect/api/workflow" + str(_id)
	to_put = to_put[0]
	resp = requests.request(method="PUT", url=url_put_data, json=to_put, headers=headers)
	if resp.status_code == 200:
		logging.info("Put data to db.")
	else:
		logging.info(resp)
	return None