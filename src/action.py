from lib.forwarder import handle_log
import os

if __name__ == "__main__":

    # get all the passed in variables
    file_name = os.environ.get("INPUT_FILE_NAME", False)
    input_data = os.environ.get("INPUT_INPUT_DATA", False)
    log_type = os.environ.get("INPUT_LOG_TYPE", "GitHubAction_CL")
    log_analytics_workspace_id = os.environ.get(
        "INPUT_LOG_ANALYTICS_WORKSPACE_ID", False
    )
    log_analytics_workspace_key = os.environ.get(
        "INPUT_LOG_ANALYTICS_WORKSPACE_KEY", False
    )

    try:
        # call handle_log function to send data to Sentinel
        handle_log(
            file_name,
            input_data,
            log_analytics_workspace_id,
            log_analytics_workspace_key,
            log_type,
        )
    except Exception as e:
        print(e)
