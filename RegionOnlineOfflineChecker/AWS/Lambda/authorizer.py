# Region Online Check Authorizer Function
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event)
    if event['headers']['x-secondlife-owner-key'] == os.environ['SecondLife_Region_Owner_Key']:
        return {
            "isAuthorized": True
        }
 
    return {
        "isAuthorized": False
    }
