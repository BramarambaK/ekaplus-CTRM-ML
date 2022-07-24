import logging
import boto3
import pickle
import spacy
import create_bucket

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET = 'spacy-nlp-model'
MODEL_KEY = 'nlp_model.pkl'
MODEL_NAME = 'nlp_model.pkl'
REGION = 'us-east-2'

model = 'en_core_web_sm'
nlp = spacy.load(model)  # load existing spaCy model

with open(MODEL_NAME, 'wb') as open_file:
    pickle.dump(nlp, open_file)

def get_bucket_names()
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()
    buckets_list = buckets['Buckets']
    buckets_name_list = [i['Name'] for i in buckets_list]
    return buckets_name_list


def upload_model_file(model):
    s3 = boto3.resource('s3')
    if S3_BUCKET in buckets_name_list:
        s3.Bucket(S3_BUCKET).upload_file(model, MODEL_KEY)
        logging.info("Uploaded model.")
    else:
        logging.info("Bucket not found. Creating a new one.")
        create_bucket.create_bucket(S3_BUCKET, REGION)
        s3.Bucket(S3_BUCKET).upload_file(model, MODEL_KEY)
        logging.info("Uploaded model.")
    return None
upload_model_file(MODEL_NAME)