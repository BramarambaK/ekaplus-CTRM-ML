import os
import json
import time
import logging
import boto3
import anomaly_api

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_event_headers_and_payload(event):
    headers_post = event['headers']
    input_body = event['body']
    input_body = input_body.rstrip('\r\n')
    logger.info(input_body)
    input_body = json.loads(input_body)
    return headers_post, input_body

def train_anomaly_(event, context):
    total_api_time = 0
    tick_ = time.time()
    logger.info('RECIEVED REQUEST TO TRAIN ANOMALY')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
        msg = anomaly_api.train_( headers_post, input_body)
        return msg
    except:
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    

def check_anomaly_(event, context):
    total_api_time = 0
    tick_ = time.time()
    logger.info('RECIEVED REQUEST TO CHECK ANOMALY')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    msg = anomaly_api.check_(headers_post, input_body)
    return msg