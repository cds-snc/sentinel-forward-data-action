import json
from lib.forwarder import handle_log
import os

if __name__ == "__main__":

    # get all the passed in variables
    fileName =os.environ["INPUT_FILE_NAME"]
    inputData =os.environ["INPUT_INPUT_DATA"]
    log_analytics_workspace_id =os.environ["INPUT_LOG-ANALYTICS-WORKSPACE-ID"]
    log_analytics_workspace_key =os.environ["INPUT_LOG-ANALYTICS-WORKSPACE-KEY"]
    
    try:
	# call handle_log function to send data to Sentinel
        handle_log(fileName, inputData, log_analytics_workspace_id, log_analytics_workspace_key, "TestData_CL")
    except Exception as e:
        print(e)
