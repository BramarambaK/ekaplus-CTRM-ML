import boto3
import logging
import pickle
import botocore
import json
import os

# S3_BUCKET = 'testing-engg'
S3_BUCKET = os.environ.get('NLP_S3_BUCKET')
training_data_files = {}

def get_training_data(input_body, headers):
    logging.info("Loading the training data.")
    try:
        if input_body['data']:
            logging.info("Training data passed in the request. Using that for training the model.")
            return input_body
    except KeyError:
        data = get_training_data_s3(headers)
        return data

def get_json_from_text(filename):
    with open(filename) as f:
        json_data = json.load(f)
    return json_data

def get_training_data_s3(headers):
    logging.info("Loading the training data file from s3.")
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    file_path_lambda = '/tmp/' + str(tenant_id) + '_' + str(app_id) + '_' + str(object_id) + '_training_file.txt'
    try:
        filename = str(headers['X-trainingFile'])
    except:
        logging.error("Pass the training data file header in the request.")
        return None
    file_key = str(tenant_id) + '/' + str(app_id) + '/nlp/' + filename + '.txt'
    logging.info(file_key)

    if file_key not in training_data_files:
        logging.info("Training data files not found in cache. Loading the training files from s3.")
        s3 = boto3.resource('s3')
        try:
            s3.Bucket(S3_BUCKET).download_file(file_key, file_path_lambda)
            logging.info("Downloaded the training data file from s3.")
            training_data_json = get_json_from_text(filename=file_path_lambda)
            logging.info("Loaded training data to json for model training.")
            training_data_files[file_key] = training_data_json
            return training_data_json
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                logging.error(e)
                logging.info("Training data file not found in s3.")
                return None
            else:
                logging.error(e)
                return None
    else:
        logging.info("Training data files found in the cache.")
        return training_data_files[file_key]