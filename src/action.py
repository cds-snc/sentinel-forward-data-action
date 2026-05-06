import os
import logzero

logzero.json()
log = logzero.logger

if __name__ == "__main__":
    # Data inputs (shared by both paths)
    file_name = os.environ.get("INPUT_FILE_NAME", False)
    input_data = os.environ.get("INPUT_INPUT_DATA", False)

    # v2 inputs (Logs Ingestion API)
    dce_endpoint = os.environ.get("INPUT_DCE_ENDPOINT", False)
    dcr_rule_id = os.environ.get("INPUT_DCR_RULE_ID", False)
    stream_name = os.environ.get("INPUT_STREAM_NAME", False)

    # v1 inputs (Data Collector API)
    workspace_id = os.environ.get("INPUT_LOG_ANALYTICS_WORKSPACE_ID", False)
    workspace_key = os.environ.get("INPUT_LOG_ANALYTICS_WORKSPACE_KEY", False)
    log_type = os.environ.get("INPUT_LOG_TYPE", False)

    has_v2 = dce_endpoint and dcr_rule_id and stream_name
    has_v1 = workspace_id and workspace_key and log_type

    try:
        if has_v2 and has_v1:
            log.error(
                "Both v1 (Data Collector) and v2 (Logs Ingestion) inputs provided. "
                "Please provide only one set of credentials."
            )
        elif has_v2:
            from lib.forwarder_v2 import handle_log

            handle_log(file_name, input_data, dce_endpoint, dcr_rule_id, stream_name)
        elif has_v1:
            from lib.forwarder import handle_log

            handle_log(file_name, input_data, workspace_id, workspace_key, log_type)
        else:
            log.error(
                "No complete set of credentials provided. "
                "Provide either v2 inputs (dce_endpoint, dcr_rule_id, stream_name) "
                "or v1 inputs (log_analytics_workspace_id, log_analytics_workspace_key, log_type)."
            )
    except Exception as e:
        print(e)
