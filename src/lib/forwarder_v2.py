import json
import os
import tempfile
import logzero
import requests
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient

logzero.json()
log = logzero.logger


# Fetch a GitHub Actions OIDC token and write it to a temporary file.
# Returns the path to the token file, or None if OIDC is not available.
def _fetch_oidc_token_file(audience="api://AzureADTokenExchange"):
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not request_url or not request_token:
        return None

    response = requests.get(
        f"{request_url}&audience={audience}",
        headers={"Authorization": f"bearer {request_token}"},
        timeout=10,
    )
    response.raise_for_status()
    token = response.json()["value"]

    token_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".token", delete=False
    )
    token_file.write(token)
    token_file.close()
    return token_file.name


# Configure Azure identity environment variables so DefaultAzureCredential
# can authenticate.  Supports client-secret and GitHub OIDC federated flows.
def _configure_azure_env(client_id, tenant_id, client_secret):
    if client_id:
        os.environ["AZURE_CLIENT_ID"] = client_id
    if tenant_id:
        os.environ["AZURE_TENANT_ID"] = tenant_id

    if client_secret:
        os.environ["AZURE_CLIENT_SECRET"] = client_secret
    elif client_id and tenant_id:
        # Attempt GitHub Actions OIDC federated credential flow
        token_file = _fetch_oidc_token_file()
        if token_file:
            os.environ["AZURE_FEDERATED_TOKEN_FILE"] = token_file
            log.info("Using GitHub Actions OIDC federated credential")
        else:
            log.warning(
                "No client_secret and OIDC token request not available. "
                "DefaultAzureCredential will attempt other credential types."
            )


# Create an authenticated LogsIngestionClient using DefaultAzureCredential.
# Accepts optional credential parameters; if provided, configures environment
# variables so that DefaultAzureCredential can authenticate.
def create_client(endpoint, client_id=None, tenant_id=None, client_secret=None):
    _configure_azure_env(client_id, tenant_id, client_secret)
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
    client_id=None,
    tenant_id=None,
    client_secret=None,
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

    client = create_client(endpoint, client_id, tenant_id, client_secret)
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
