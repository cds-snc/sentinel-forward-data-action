from lib.forwarder import handle_log
import os

if __name__ == "__main__":

    # get all the passed in variables
    fileName = os.environ.get("INPUT_FILE_NAME", False)
    inputData = os.environ.get("INPUT_INPUT_DATA", False)
    logType = os.environ.get("INPUT_LOG_TYPE", "GitHubAction_CL")
    log_analytics_workspace_id = os.environ.get(
        "INPUT_LOG_ANALYTICS_WORKSPACE_ID", False
    )
    log_analytics_workspace_key = os.environ.get(
        "INPUT_LOG_ANALYTICS_WORKSPACE_KEY", False
    )

    try:
        # call handle_log function to send data to Sentinel
        handle_log(
            fileName,
            inputData,
            log_analytics_workspace_id,
            log_analytics_workspace_key,
            logType,
        )
    except Exception as e:
        print(e)
