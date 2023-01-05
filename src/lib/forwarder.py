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


def handle_log(filePath, input_data, customer_id, shared_key,log_type):
    if customer_id is False or shared_key is False:
        log.error("Missing required environment variables customer_id, log_type, or shared_key")
        return False

    if input_data is False:
        log.error("Missing required input data")
        return False

    # send the data to Azure Sentinel
    return post_data(customer_id, shared_key, input_data, log_type)



def build_signature(
    customer_id, shared_key, date, content_length, method, content_type, resource
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
    decoded_key = base64.b64decode(shared_key)
    encoded_hash = base64.b64encode(
        hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
    ).decode()
    authorization = "SharedKey {}:{}".format(customer_id, encoded_hash)
    return authorization


def post_data(customer_id, shared_key, body, log_type):
    method = "POST"
    content_type = "application/json"
    resource = "/api/logs"
    rfc1123date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_length = len(body)
    signature = build_signature(
        customer_id,
        shared_key,
        rfc1123date,
        content_length,
        method,
        content_type,
        resource,
    )
    uri = (
        "https://"
        + customer_id
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
        log.info(response.text)
        #log.info(f"Response code: {response.status_code}, log type: {log_type}")
        return True
    else:
        log.error(response.text)
        #log.error(f"Response code: {response.status_code}, log type: {log_type}")
        return False