import base64
import datetime
import gzip
import hashlib
import hmac
import io
import json
import os
import re

import logzero
import requests

logzero.json()
log = logzero.logger

# determine if a string is a json object. If it is, it returns True. Otherwise, false is returned. 
def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True


# Convert the input data to a JSON object
def convert_to_json(input_data):
    if is_json(input_data):
        return input_data
    else:
        try:
            body = {}
            body['Message'] = input_data
            return json.dumps(body)
        except Exception as e:
            log.error("Failed to convert input data to JSON")
            log.error(e)
            return False
    
    
    
def process_file_contents(file_name, log_analytics_workspace_id, log_analytics_workspace_key, input_data, log_type):
    with open(file_name, 'r') as file:
        lines = file.readlines()
    for line in lines:
        post_data(log_analytics_workspace_id, log_analytics_workspace_key, convert_to_json(line), log_type)
    

def handle_log(file_name, input_data, log_analytics_workspace_id, log_analytics_workspace_key,log_type):    
    if log_analytics_workspace_id is False or log_analytics_workspace_key is False:
        log.error("Missing required environment variables log_analytics_workspace_id  or log_analytics_workspace_key")
        return False

    if log_type is False:
        log.error("Missing required log type for Sentinel")
        return False

    if input_data is False and file_name is False:
        log.error("Missing required input data or file name")
        return False
    
    
    if input_data:
        # send the data to Azure Sentinel
        post_data(log_analytics_workspace_id, log_analytics_workspace_key, convert_to_json(input_data), log_type)
        # return True
        
        
    if file_name:
        try:
            # process each line in the file and send it to Azure Sentinel
            process_file_contents(file_name, log_analytics_workspace_id, log_analytics_workspace_key, input_data, log_type)
            # return True
        except Exception as e:
            print(e)
            return False     
    return True



def build_signature(
    log_analytics_workspace_id, log_analytics_workspace_key, date, content_length, method, content_type, resource
):
    x_headers = "x-ms-date:" + date
    string_to_hash = (
        method
        + "\n"
        + str(content_length)
        + "\n"
        + content_type
        + "\n"
        + x_headers
        + "\n"
        + resource
    )
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(log_analytics_workspace_key)
    encoded_hash = base64.b64encode(
        hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
    ).decode()
    authorization = "SharedKey {}:{}".format(log_analytics_workspace_id, encoded_hash)
    return authorization


def post_data(log_analytics_workspace_id, log_analytics_workspace_key, body, log_type):
    method = "POST"
    content_type = "application/json"
    resource = "/api/logs"
    rfc1123date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_length = len(body)
    signature = build_signature(
        log_analytics_workspace_id,
        log_analytics_workspace_key,
        rfc1123date,
        content_length,
        method,
        content_type,
        resource,
    )
    uri = (
        "https://"
        + log_analytics_workspace_id
        + ".ods.opinsights.azure.com"
        + resource
        + "?api-version=2016-04-01"
    )

    headers = {
        "content-type": content_type,
        "Authorization": signature,
        "Log-Type": log_type,
        "x-ms-date": rfc1123date,
    }

    response = requests.post(uri, data=body, headers=headers)
    if response.status_code >= 200 and response.status_code <= 299:
        log.info(f"Response code: {response.status_code}, log type: {log_type}")
        return True
    else:
        log.error(f"Response code: {response.status_code}, log type: {log_type}")
        return False
