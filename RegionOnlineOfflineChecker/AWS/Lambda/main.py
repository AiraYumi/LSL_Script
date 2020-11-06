# Region Online Checker
import json
import os
import boto3
import logging
import urllib
import socket

ENV_WEBHOOK_URL = os.environ['WEBHOOK_URL']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('dynamodb')

def lambda_handler(event, context):
    logger.info(event)
    if ('headers' in event) and ('x-secondlife-owner-key' in event['headers']):
        # Slackにリージョンの起動を通知
        message = "リージョン「%s」はオンラインです" % event['headers']['x-secondlife-region']
        slack_message = {
            "username": "SLRegionStatusObject",
            "attachments": [{ "text" : message }]
        }
        params = json.dumps(slack_message).encode("utf-8")
        
        method = "POST"
        headers = {"Content-Type" : "application/json"}
        req = urllib.request.Request(ENV_WEBHOOK_URL, data=params, method=method, headers=headers)
        with urllib.request.urlopen(req) as res:
            logger.info(res.read().decode("utf-8"))
        
		# DynamoDBにリージョンのステータス(オンライン or オフライン)を記録
        client.update_item(
            TableName='SLRegionCheckTarget',
            Key={
                'Region':{ 'S':event['headers']['x-secondlife-region'] }
            },
            UpdateExpression='set #s = :status, #u = :url',
            ExpressionAttributeNames={
                '#s':'Status',
                '#u':'URL'
            },
            ExpressionAttributeValues={
                ':status':{ 'S':'Online' },
                ':url':{ 'S': event['body'] }
            }
        )
		
		# LSL Scriptに返送される文字列
        rtn_message = "We changed the request URL because the region restarted.";
    else:
        records = client.scan(
            TableName='SLRegionCheckTarget'
        )
        
        for record in records['Items']:
            region = list(record['Region'].values())[0]
            status = list(record['Status'].values())[0]
            url = list(record['URL'].values())[0]
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, None, 10) as res:
                    body = res.read()
                    logger.info(body)
            except (socket.timeout, urllib.error.HTTPError) as err:
                if status == "Online":
                    logger.error(err)
                    
                    # Slackにリージョンがオンライン→オフライン状態に遷移したことを通知
                    message = "リージョン「%s」はオフラインです" % region
                    slack_message = {
                        "username": "SLRegionStatusObject",
                        "attachments": [{ "text" : message }]
                    }
                    params = json.dumps(slack_message).encode("utf-8")
                    
                    method = "POST"
                    headers = {"Content-Type" : "application/json"}
                    req = urllib.request.Request(ENV_WEBHOOK_URL, data=params, method=method, headers=headers)
                    with urllib.request.urlopen(req) as res:
                        logger.info(res.read().decode("utf-8"))
                    
                    client.update_item(
                        TableName='SLRegionCheckTarget',
                        Key={
                            'Region':{ 'S':region }
                        },
                        UpdateExpression='set #s = :status',
                        ExpressionAttributeNames={
                            '#s':'Status'
                        },
                        ExpressionAttributeValues={
                            ':status':{'S' : 'Offline'}
                        }
                    )
		rtn_message = "OK";
        
    return rtn_message
