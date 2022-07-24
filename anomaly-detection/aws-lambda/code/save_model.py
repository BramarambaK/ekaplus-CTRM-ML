import io
import os
import logging
import pickle
import boto3

S3_BUCKET = os.environ.get('ANOMALY_S3_BUCKET')
# S3_BUCKET = 'testing-engg'

def save_model(bucket_name, model_file, headers):
    logging.info("Getting the s3 resource to save the model file.")
    s3_resource = boto3.resource('s3')
    logging.info(model_file)
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    user_id = headers['userId']
    model_key = str(tenant_id) + '/' + str(app_id) + '/anomaly/' + str(object_id) + '_' + str(user_id) + '_anomaly.pkl'
    print(f"The model key is {model_key}")
    try:
        pickle_byte_obj = pickle.dumps(model_file)
        s3_resource.Object(bucket_name, model_key).put(Body=pickle_byte_obj)
        logging.info("Put the model file in s3 bucket.")
        print("Put the model file in s3 bucket.")
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