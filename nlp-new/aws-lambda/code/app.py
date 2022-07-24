import json
import time
import logging
import train_model
import predict
import authenticate
import load_model
import save_model
import get_training_data
import load_model_and_tag_map

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_event_headers_and_payload(event):
    headers_post = event['headers']
    input_body = event['body']
    input_body = input_body.rstrip('\r\n')
    logger.info(input_body)
    input_body = json.loads(input_body)
    headers_post["X-Object"] = input_body["object"]
    headers_post["X-appId"] = input_body["appId"]
    tenant_id = headers_post['X-TenantID']
    return headers_post, input_body

def process_sentence(event, context):
    total_api_time = 0
    tick_ = time.time()
    logger.info('RECIEVED REQUEST TO TAG SENTENCE')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    try:
        authentication_response = authenticate.authenticate_and_validate_user(headers_post)
    except:
        logging.info("Error while validating platform token.")
        res = {"statusCode": 200, "body":json.dumps({"msg":"Error while validating platform token."})}
        return res
    if authentication_response is not None:
        if authentication_response.status_code == 200:
            logger.info("Authentication token is valid.")
            logger.info("Calling the get tags function.")
            sent = input_body["sentence"]
            # model = load_model.load_model_file(headers=headers_post)
            model, tag_map = load_model_and_tag_map.load_model_tag_map_file(headers=headers_post)
            if model is None:
                return {"statusCode": 200,"body": json.dumps({"message": "Model not found. Train a model to get predictions."})}
            else:
                entities_ = predict.get_prediction(sent, model, headers_post, tag_map)
                entities_ = predict.map_text_to_root(headers_post, input_body, entities_)
                logger.info(entities_)
                res = {"statusCode": 200, "body":json.dumps({"tags":entities_})}
                total_api_time += time.time() - tick_
                logger.info(f'Total API time : {total_api_time}')
                return res
        else:
            res = {"statusCode": 200, "body":json.dumps({"msg":"Authorization is not valid."})}
            total_api_time += time.time() - tick_
            logger.info(f'Total API time : {total_api_time}')
            return res

def train(event, context):
    total_api_time = 0
    tick_ = time.time()
    logger.info('RECIEVED REQUEST TO TRAIN NLP MODEL.')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body  = get_event_headers_and_payload(event)
    except:
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    try:
        authentication_response = authenticate.authenticate_and_validate_user(headers_post)
    except:
        logging.info("Error while validating platform token.")
        res = {"statusCode": 200, "body":json.dumps({"msg":"Error while validating platform token."})}
        return res

    if authentication_response is not None:
        if authentication_response.status_code == 200:
            logger.info("Authentication token is valid.")
            logger.info("Calling the train model function.")
            try:
                data = get_training_data.get_training_data(input_body, headers_post)
                if 'mapping' in input_body:
                    tag_map = input_body['mapping']
                else:
                    tag_map = None
                train_model.main(model='en_core_web_sm', user_input=data, headers=headers_post, tag_map=tag_map)
                msg = {"statusCode": 200, "body":json.dumps({"msg":"Trained the nlp model."})}
                return msg
            except Exception as e:
                logging.error(e)
                msg = {"statusCode": 200, "body":json.dumps({"msg":"Error while training the nlp model."})}
                return msg
        else:
            res = {"statusCode": 200, "body":json.dumps({"msg":"Authorization is not valid."})}
            total_api_time += time.time() - tick_
            logger.info(f'Total API time : {total_api_time}')
            return res

def reset(event, context):
    total_api_time = 0
    tick_ = time.time()
    logger.info('RECIEVED REQUEST TO DELETE MODEL')
    logger.info('EVENT OBJECT')
    logger.info(event)
    try:
        headers_post, input_body = get_event_headers_and_payload(event)
    except:
        return {"statusCode": 200,"body": json.dumps({"message": "Please check the request headers and body."})}
    try:
        authentication_response = authenticate.authenticate_and_validate_user(headers_post)
    except:
        logging.info("Error while validating platform token.")
        res = {"statusCode": 200, "body":json.dumps({"msg":"Error while validating platform token."})}
        return res
    if authentication_response is not None:
        if authentication_response.status_code == 200:
            logger.info("Authentication token is valid.")
            logger.info("Calling the delete model function.")
            res = load_model.delete_model_file(headers=headers_post)
            if res['ResponseMetadata']['HTTPStatusCode'] == 204:
                res = {"statusCode": 200, "body":json.dumps({"msg":"Deleted the model file from s3 bucket and cleared cache."})}
                total_api_time += time.time() - tick_
                logger.info(f'Total API time : {total_api_time}')
                return res
        else:
            res = {"statusCode": 200, "body":json.dumps({"msg":"Authorization is not valid."})}
            total_api_time += time.time() - tick_
            logger.info(f'Total API time : {total_api_time}')
            return res