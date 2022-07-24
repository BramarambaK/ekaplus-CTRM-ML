import sys
import os
from flask import Flask, request, jsonify
import requests
import logging
import token_matcher

logger = logging.getLogger()
logger.setLevel(logging.INFO)
###########
# Constants
###########

port = 7878

def get_headers_and_data(request):
    headers_post, input_body = dict(request.headers), dict(request.json)
    return headers_post, input_body


app = Flask(__name__)
@app.route("/tag-text", methods = ['POST'])
def train_():
    headers_post, input_body = get_headers_and_data(request)
    # logger.info(headers_post)
    # logger.info(input_body)
    tagged_data, is_v1_prior  = token_matcher.tag_text(headers_post, input_body)
    print(f"The tagged data is {tagged_data} and the is_v1_prior priority is \n {is_v1_prior}")
    return {"tags":tagged_data}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)