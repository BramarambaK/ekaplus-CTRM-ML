import logging
from flask import Flask, request, jsonify
import requests
from pathlib import Path
import spacy
import train_model
from predict import load_trained_model
from reset_training import reset

logger = logging.getLogger()
logger.setLevel(logging.INFO)
port = 7676

# Constants
MODEL_DIR = 'D:/work/nlp/local/model'
MODEL_NAME = 'en_core_web_sm'

# Request headers
PLATFORM_URL = 'X-PlatformUrl'
ACCESS_TOKEN = 'X-AccessToken'
APP_ID = 'X-appId'
OBJECT_ID = 'X-Object'

# messages
trained_model = "Trained the nlp model."
reset_api = "Reset the NLP model and forgot previous training."
invalid_auth_message = {"msg":"Authorization token is invalid."}


def get_headers_and_data(request):
    logging.info("Parsing the request headers and body.")
    headers_post, input_body = request.headers, request.json
    return headers_post, input_body

def get_model_dir(headers):
    app_id = headers[APP_ID]
    object_id = headers[OBJECT_ID]
    model_dir = MODEL_DIR + '/' + str(app_id) + '/' + str(object_id)
    return model_dir

def authenticate_user(headers):
    platform_url = headers[PLATFORM_URL]
    authentication_url = platform_url + '/cac-security/api/userinfo'
    platform_token = headers[ACCESS_TOKEN]
    headers_ = {'Authorization':platform_token}
    response = requests.get(url=authentication_url, headers=headers_)
    if response.status_code == 200:
        return True
    else:
        return False


app = Flask(__name__)
@app.route("/process-sentence", methods = ['POST'])
def process_():
    logging.info("Processing input sentence for tagging.")
    headers, body = get_headers_and_data(request)
    if authenticate_user(headers):
        sentence = body["sentence"]
        model_dir = get_model_dir(headers)
        entities_ = load_trained_model(sentence, model_dir)
        return entities_
    else:
        return invalid_auth_message

@app.route("/train-nlp", methods = ['POST'])
def train():
    logging.info("Invoked the training api.")
    headers, body = get_headers_and_data(request)
    if authenticate_user(headers):
        model_dir = get_model_dir(headers)
        train_model.main(model=MODEL_NAME, output_dir=model_dir, user_input=body)
        msg = {"msg":trained_model}
        logging.info(trained_model)
        return msg
    else:
        return invalid_auth_message


@app.route("/reset-nlp", methods=['POST'])
def reset_():
    logging.info("Invoked the reset api.")
    headers, body = get_headers_and_data(request)
    if authenticate_user(headers):
        model_dir = get_model_dir(headers)
        msg = reset(model_dir)
        return msg
    else:
        return invalid_auth_message

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)