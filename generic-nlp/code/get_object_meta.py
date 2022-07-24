"""Fetch the object meta to create the dependnece matrix"""

import requests
import logging
import json
import _pickle as cPickle


def call_meta_api(get_meta_url, headers, payload):
	"""Call the object meta API to fetch the object meta data."""
	json_data = None
	if get_meta_url is not None:
		headers['Content-Type'] = 'application/json'
		payload_ = str(payload)
		payload_ = payload_.replace(" ", "")
		payload_ = payload_.replace("'", '"')
		response = requests.post(url=get_meta_url, data=payload_, headers=headers)
		json_data = response.json()
		return json_data
	else:
		msg = "Error in fetching meta for the object."
		logging.info(msg)
		return json_data