import json
import logging
import boto3
import botocore
import os
import csv
import read_csv_file

S3_BUCKET = os.environ.get('NLP_S3_BUCKET')

response_map_files = {}

def save_response_map(bucket_name, response_map_file, headers):
    logging.info("Getting the s3 resource to save the response map file.")
    s3_resource = boto3.resource('s3')
    logging.info(response_map_file)
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    response_map_key = '/tmp/' + str(app_id) + '_' + str(object_id) + '_' + 'nlp.json'
    try:
        response_map_file_ = json.dumps(response_map_file).encode()
        s3_resource.Object(bucket_name, response_map_key).put(Body=response_map_file_)
        logging.info("Put the response map file in s3 bucket.")
    except Exception as e:
        logging.error(e)
        logging.info("Error while saving response map file to s3.")
    return None

def save_response_map_to_s3(response_map, headers):
    try:
        logging.info("Calling the save response map function.")
        save_response_map(bucket_name=S3_BUCKET, response_map_file=response_map, headers=headers)
    except:
        logging.info("Error while saving a response function.")
        logging.error(e)

def save_response(response_map, headers):
    # save model to output directory
    try:
        logging.info("Calling the save response map function.")
        save_response_map_to_s3(response_map=response_map, headers=headers)
    except Exception as e:
        logging.error(e)
        logging.error("Error while saving the response map to s3.")
    return None

def load_response_map(headers):
    logging.info("Loading the response map file from s3.")
    app_id = headers['X-appId']
    object_id = headers['X-Object']
    tenant_id = headers['X-TenantID']
    file_path_lambda = '/tmp/' + str(tenant_id) + '_' + str(app_id) + '_' + str(object_id) + 'map.csv'
    try:
        filename = str(headers['X-responseFile'])
    except:
        logging.error("Pass the response file header in the request.")
        return None
    file_key = str(tenant_id) + '/' + str(app_id) + '/nlp/' + filename + '.csv'
    logging.info(file_key)

    if file_key not in response_map_files:
        logging.info("Response map files not found in cache. Loading the files from s3.")
        s3 = boto3.resource('s3')
        try:
            s3.Bucket(S3_BUCKET).download_file(file_key, file_path_lambda)
            logging.info("Downloaded the response mapping file from s3.")
            response_map = read_csv_file.read_csv_file(filename=file_path_lambda)
            logging.info("Converted csv to json for prediction.")
            response_map_files[file_key] = response_map
            return response_map
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                logging.error(e)
                logging.info("Response map file not found in s3.")
                return None
            else:
                logging.error(e)
                return None
    else:
        logging.info("Response map files found in the cache.")
        return response_map_files[file_key]