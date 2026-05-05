import json
import os
import logzero
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient

logzero.json()
log = logzero.logger


# Create an authenticated LogsIngestionClient using DefaultAzureCredential.
# In GitHub Actions: picks up OIDC token from azure/login.
# Locally: picks up AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET.
def create_client(endpoint):
    credential = DefaultAzureCredential()
    return LogsIngestionClient(endpoint=endpoint, credential=credential)


# Determine if a string is a json object.
def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


# Convert input data to a list of log entry dicts for the Logs Ingestion API.
def convert_to_log_entries(input_data):
    if is_json(input_data):
        parsed = json.loads(input_data)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    else:
        return [{"Message": input_data}]


# Process file contents and return a list of log entry dicts.
def process_file_to_entries(file_name):
    entries = []
    with open(file_name, "r", encoding="utf-8") as file:
        if file_name.endswith(".json"):
            json_object = json.load(file)
            if isinstance(json_object, list):
                entries = json_object
            else:
                entries = [json_object]
        else:
            lines = file.readlines()
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if is_json(stripped):
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        entries.extend(parsed)
                    else:
                        entries.append(parsed)
                else:
                    entries.append({"Message": stripped})
    log.info(f"File name: {file_name}, file size: {os.path.getsize(file_name)}")
    return entries


# Upload log entries to Azure Monitor via the Logs Ingestion API.
def upload_data(client, dcr_rule_id, stream_name, logs):
    if not logs:
        log.warning("No data to send to Azure Monitor")
        return False

    try:
        client.upload(rule_id=dcr_rule_id, stream_name=stream_name, logs=logs)
        log.info(f"Uploaded {len(logs)} entries, stream: {stream_name}")
        return True
    except HttpResponseError as e:
        log.error(f"Upload failed: {e}")
        return False


# Handle data sent by the github action.
def handle_log(
    file_name,
    input_data,
    endpoint,
    dcr_rule_id,
    stream_name,
):
    if endpoint is False or dcr_rule_id is False or stream_name is False:
        log.error(
            "Missing required environment variables: "
            "dce_endpoint, dcr_rule_id, or stream_name"
        )
        return False

    if input_data is False and file_name is False:
        log.error("Missing required input data or file name")
        return False

    client = create_client(endpoint)
    all_entries = []

    if input_data:
        all_entries.extend(convert_to_log_entries(input_data))

    if file_name:
        try:
            all_entries.extend(process_file_to_entries(file_name))
        except Exception as e:
            log.error(f"Failed to process file: {e}")
            return False

    return upload_data(client, dcr_rule_id, stream_name, all_entries)
