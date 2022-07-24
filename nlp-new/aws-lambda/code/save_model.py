import logging
import pickle
import boto3
import io
import os

S3_BUCKET = os.environ.get('NLP_S3_BUCKET')

def save_model(bucket_name, model_file, headers):
    logging.info("Getting the s3 resource to save the model file.")
    s3_resource = boto3.resource('s3')
    logging.info(model_file)
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    model_key = str(tenant_id) + '/' + str(app_id) + '/nlp/' + str(object_id) + '_' + 'nlp.pkl'
    try:
        pickle_byte_obj = pickle.dumps(model_file)
        s3_resource.Object(bucket_name, model_key).put(Body=pickle_byte_obj)
        logging.info("Put the model file in s3 bucket.")
    except Exception as e:
        logging.error(e)
        logging.info("Error while saving model file to s3.")
    return None

def save_model_to_s3(model, headers):
    try:
        logging.info("Saving the model to s3.")
        save_model(bucket_name=S3_BUCKET, model_file=model, headers=headers)
    except Exception as e:
        logging.info("Error while saving model to s3.")
        logging.error(e)