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


def post_data(host_port, app_id, recommendation_object , to_post, headers):
	"""Post data to mongo if data doesn't exist previously."""
	url_post_data = host_port + "/data/" + app_id + "/" + recommendation_object
	resp = requests.request(method="POST", url=url_post_data, json=to_post, headers=headers)
	if resp.status_code == 200:
		logging.info("Posted data to db.")
	else:
		print(resp)
	return None

def put_data(host_port, app_id, recommendation_object , to_put, headers, _id):
	"""Put data to mongo if data exists for the users."""
	url_put_data = host_port + "/data/" + app_id + "/" + recommendation_object + '/' + str(_id)
	to_put = to_put[0]
	resp = requests.request(method="PUT", url=url_put_data, json=to_put, headers=headers)
	if resp.status_code == 200:
		logging.info("Put data to db.")
	else:
		print(resp)
	return None