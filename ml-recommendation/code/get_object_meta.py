"""Fetch the object meta to create the dependnece matrix"""

import requests
import logging
import json
import _pickle as cPickle
import get_data_api

def call_meta_api(get_meta_url, auth, tenant, obj):
	"""Call the object meta API to fetch the object meta data."""
	json_data = None
	if get_meta_url is not None:
		if obj is not None:
			get_meta_url = get_meta_url + obj
			headers = {"Authorization":auth, "X-TenantID":tenant}
			response = requests.request(method='GET', url=get_meta_url, headers=headers)
			json_data = response.json()
			if not json_data:
				get_meta_url = get_meta_url + obj
				headers = {"Authorization":auth, "X-TenantID":tenant}
				response = requests.request(method='GET', url=get_meta_url, headers=headers)
				json_data = response.json()
			else:
				pass
		else:
			msg = "Pass the object Id in the body of the API call."
			return json_data
	else:
		msg = "Add appropriate host in the environment variables."
	return json_data
