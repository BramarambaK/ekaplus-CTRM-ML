import logging
import pickle
import boto3
import boto3.session
import pickle
import os
from io import BytesIO

S3_BUCKET = os.environ.get('NLP_S3_BUCKET')

model_files = {}

def load_model_file(headers):
    logging.info("Loading the model file from s3.")
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    model_path = '/tmp/' + str(tenant_id) + '_' + str(app_id) + '_' + str(object_id)
    model_key = str(tenant_id) + '/' + str(app_id) + '/nlp/' + str(object_id) + '_' + 'nlp.pkl'
    if model_key not in model_files:
        logging.info("Model files not found in cache. Loading the model from s3.")
        s3 = boto3.resource('s3')
        try:
            s3.Bucket(S3_BUCKET).download_file(model_key, model_path)
            with open(model_path, 'rb') as data:
                nlp_model = pickle.load(data)
            logging.info("Loaded the model from s3.")
            logging.info(nlp_model)
            model_files[model_key] = nlp_model
            return nlp_model
        except Exception as e:
            logging.error(e)
            logging.info("Error while loading model file from s3.")
    else:
        logging.info("Model files found in the cache.")
        return model_files[model_key]

def get_model(headers):
    nlp_model = load_model_file(headers=headers)
    if nlp_model is not None:
        return nlp_model
    else:
        return None

def delete_s3_obj(model_key):
    logging.info("Getting the s3 resource to delete the model file.")
    s3 = boto3.client('s3')
    resp = s3.delete_object(Bucket=S3_BUCKET, Key=model_key)
    logging.info(resp)
    return resp 

def delete_model_file(headers):
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    model_key = str(tenant_id) + '/' + str(app_id) + '/nlp/' + str(object_id) + '_' + 'nlp.pkl'
    logging.info("Clearing model from cache.")
    if str(model_key) not in model_files:
        pass
    else:
        model_files.pop(str(model_key), None)
        logging.info("Cleared model files from cache.")
    resp = delete_s3_obj(model_key)
    return resp