import os
import logging
import pickle
import boto3
import boto3.session
from io import BytesIO

S3_BUCKET = os.environ.get('ANOMALY_S3_BUCKET')
# S3_BUCKET = 'testing-engg'

fit_and_ecdf_map = {}
model_files = {}
ecdf_files = {}
cols_data_files = {}

def load_model_files(headers):
    logging.info("Loading the model file from s3.")
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    user_id = headers['userId']
    _key = str(tenant_id) + '_' + str(app_id) + '_' + str(object_id) + '_' + str(user_id)
    files_key = str(tenant_id) + '/' + str(app_id) + '/anomaly/' + str(object_id) + '_' + str(user_id) + '_anomaly.pkl'
    model_path = '/tmp/' + _key
    # model_path = 'D:/work/anomaly-detection/models-and-data/' + _key

    if _key not in fit_and_ecdf_map:
        logging.info("Model files not found in cache. Loading the model from s3.")
        s3 = boto3.resource('s3')
        try:
            s3.Bucket(S3_BUCKET).download_file(files_key, model_path)
            with open(model_path, 'rb') as data:
                fit_and_ecdf = pickle.load(data)
            # logging.info("Loaded the model files from s3.")
            print("Loaded the model files from s3.")
            anomaly_model = fit_and_ecdf['fit']
            ecdf = fit_and_ecdf['ecdf']
            cols_data = fit_and_ecdf['cols_data']
            logging.info(anomaly_model)
            logging.info(ecdf)
            model_files[_key] = anomaly_model
            ecdf_files[_key] = ecdf
            cols_data_files[_key] = cols_data
            fit_and_ecdf_map[_key] = fit_and_ecdf
            return anomaly_model, ecdf, cols_data
        except Exception as e:
            logging.error(e)
            logging.info("Error while loading model file from s3.")
            return None, None, None
    else:
        logging.info("Model files found in the cache.")
        return model_files[_key], ecdf_files[_key], cols_data_files[_key]

def get_model(headers):
    anomaly_model, ecdf, cols_data = load_model_files(headers=headers)
    if anomaly_model is not None:
        return anomaly_model
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