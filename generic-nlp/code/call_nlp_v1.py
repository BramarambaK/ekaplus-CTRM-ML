import os
import sys
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Headers
logical_resource_id = 'ProcessSentenceFunction'
stack_name = os.environ.get('STACK_NAME')

def get_physical_resource(logical_resource_id, stack_name):
    cfn_client = boto3.client('cloudformation')
    logger.info("Call to get the stack resources:")
    response = cfn_client.describe_stack_resources(StackName=stack_name, LogicalResourceId=logical_resource_id)
    logger.info("The stack resource to be invoked is:")
    logger.info(response)
    for i in response['StackResources']:
        if i['LogicalResourceId'] == logical_resource_id:
            physical_resource_id = i['PhysicalResourceId']
        else:
            logger.info("The stack does not have the child lambda function.")
            physical_resource_id = logical_resource_id
    logger.info(f"The physical resource id of the function to be invoked is : {physical_resource_id}")
    return physical_resource_id

def invoke_child_lambda(physical_resource_id, event):
    lambda_client = boto3.client('lambda')
    resp = lambda_client.invoke(FunctionName=physical_resource_id, InvocationType='RequestResponse', Payload=json.dumps(event))
    # logger.info(f"response:{resp}")
    tagged_text = resp['Payload'].read()
    return tagged_text

def invoke(event):
    logger.info('RECIEVED REQUEST TO PROCESS SENTENCE USING NLP V1.')
    logger.info('EVENT OBJECT')
    logger.info(event)
    physical_resource_id = get_physical_resource(logical_resource_id, stack_name)
    tagged_text = invoke_child_lambda(physical_resource_id, event)
    res = {"statusCode": 200,"body": json.dumps({"message":"Invoked the lambda function to train for an user."})}
    logger.info(f"{res}")
    logger.info(f"Got the tagged data from process sentence v1: {tagged_text}")
    return tagged_text