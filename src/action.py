#!/usr/local/bin/python3

import argparse
import json
import sys
from lib.forwarder import handle_log

parser = argparse.ArgumentParser()
# TODO: Make sure that we set the required values properly
parser.add_argument('--filePath', type=str, required=False,  help='The filepath where the logs are stored from the previous github action step')
parser.add_argument('--inputData', type=str, required=False,  help='The input data to send to Azure Sentinel')
parser.add_argument('--log-analytics-workspace-id', type=str, required=True,  help='The Azure Sentinel workspace ID')
parser.add_argument('--log-analytics-workspace-key', type=str, required=True,  help='The Azure Sentinel workspace key')   

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        handle_log(args.filePath, json.loads(args.inputData), args.log_analytics_workspace_id, args.log_analytics_workspace_key, "TestData_CL")
    except Exception as e:
        print(e)
        sys.exit(1)
