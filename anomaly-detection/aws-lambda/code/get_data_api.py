import os
import sys
import requests
import logging

def get_data(get_data_url, headers, body, method):
	"""Make API calls to get the data for the requested app.
		Fetch the data from API for training the model.
	    Using the requests library.
	    Get the input headers from the POST request made when the train recommendation model API is called.
	    json_data that will be used as input to the model.
	    construct url to get the data """

	json_data = None
	if get_data_url is not None:
		headers['Content-Type'] = 'application/json'
		payload_ = str(body)
		# payload_ = payload_.replace(" ", "")
		payload_ = payload_.replace("'", '"')
		response = requests.request(method=str(method), url=get_data_url, data=payload_, headers=headers)
		json_data = response.json()
		# print(f"The json response from data API call is : {json_data}")
		# print(f"The URL is : {get_data_url}")
		try:
			json_data = json_data['data']
			logging.info("Fetched the training data.")
		except KeyError:
			msg = "The key 'data' was not found in the response."
			logging.info(msg)
			return None
	else:
		msg = "Add the appropriate host in the environment variables."
		logging.info(msg)
	return json_data

def get_paginated_data(get_data_url, headers, body, method, paginated=None):
	if paginated is True:
		data_list = []
		ctr = 0
		start = 0
		limit = 10
		while True:
			body["pagination"] = {"start":start, "limit":limit}
			ctr += 1
			# print(f"The data URL is : {get_data_url}")
			data = get_data(get_data_url=get_data_url, headers=headers, body=body, method=method)
			if data is not None:
				data_list = data_list + data
				num_data_received = len(data)
			else:
				break
			# print(f"The start parameter is :{start}, limit is {limit}. The length of data recieved is {num_data_received}.")
			if num_data_received == limit:
				start += len(data)
				limit += len(data)
				continue
			else:
				break
	else:
		data_list = get_data(get_data_url=get_data_url, headers=headers, body=body, method=method)
	print(f"Total length of the data received is : {len(data_list)}")
	return data_list