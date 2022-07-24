import os
import sys
import requests

def get_data(get_data_url, headers, body, method):
	"""Make API calls to get the data for the requested app.
		Fetch the data from API for training the model.
	    Using the requests library.
	    Get the input headers from the POST request made when the train recommendation model API is called.
	    json_data that will be used as input to the model.
	    construct url to get the data """

	json_data = None
	if get_data_url is not None:
		response = requests.request(method=str(method), url=get_data_url, json=body, headers=headers)
		json_data = response.json()
		# print(response)
		try:
			json_data = json_data['data']
			print("Fetched the training data.")
		except KeyError:
			msg = "The key 'data' was not found in the response."
			print(msg)
			return None
	else:
		msg = "Add the appropriate host in the environment variables."
		print(msg)
	return json_data


def get_paginated_data(get_data_url, headers, body, method, paginated=None):
	if paginated is True:
		data_list = []
		ctr = 0
		start = 0
		limit = 10
		while True:
			print("Pagination limits :\n", start, limit)
			body["pagination"] = {"start":start, "limit":limit}
			ctr += 1
			data = get_data(get_data_url=get_data_url, headers=headers, body=body, method=method)
			data_list = data_list + data
			num_data_received = len(data)
			if num_data_received == limit:
				start += len(data)
				limit += len(data)
				continue
			else:
				break
	else:
		data_list = get_data(get_data_url=get_data_url, headers=headers, body=body, method=method)
	return data_list