import os
import sys
import requests

def get_data(get_data_url, headers, body, method):
	"""Make API calls to get the data for the requested app.
	Fetch the data from API for training the model.
	    Using the requests library.
	    Get the input headers from the POST request made i.e.
	    when the train recommendation model API is called.
	    json_data that will be used as input to the model.
	    construct url to get the data """
	json_data = None
	if get_data_url is not None:
		response = requests.request(method=str(method), url=get_data_url, json=body, headers=headers)
		json_data = response.json()
		try:
			json_data = json_data['data']
			print("Got the data.")
		except KeyError as e:
			msg = "The key 'data' was not found in the response."
			print(msg)
			return None
	else:
		msg = "Add the appropriate host in the environment variables."
		print(msg) 
	return json_data