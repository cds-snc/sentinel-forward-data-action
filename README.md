
# Send data to Azure Sentinel Github-action

A GitHub action that sends data to Azure Sentinel from a previous GitHub action. It can either take as inputs a file name or input data that is either plain text or json format. A Sentinel log_type or table name will need to be specified when using the action and the passed in data will be stored in the indicated table name. 


### Usage

```yaml
     - name: "Post results to Sentinel"
        uses: cds-snc/sentinel-forward-data-action@main
        with:
          file_name: file-name.json
          input_data: "Data to be sent to Sentinel"
          log_type: "TestData_CL"
          log_analytics_workspace_id: ${{ secrets.LOG_ANALYTICS_WORKSPACE_ID }}
          log_analytics_workspace_key: ${{ secrets.LOG_ANALYTICS_WORKSPACE_KEY }}
```

### Action inputs

All inputs except log_type, log_analytics_workspace_id and log_analytics_workspace_key are **optional**. 


| Name                          | Description      | Mandatory   |
------------------------------- | -----------------|-------------|
| `file_name`                   | File name that will be read by the github action and each line will be processed and sent to Sentinel. The file can be either text or json format.   |  False |  
| `input_data`                  | Input data to be sent to Sentinel. The data can be either text or json format. | False |        
| `log_type`                    | The table name in Sentinel that the data will be stored at.  | True |
| `log_analytics_workspace_id`  | Sentinel workspace id that is currently stored in GitHub secrets. | True |            
| `log_analytics_workspace_key` | Sentinel workspace key which is currently stored in GitHub secrets. | True |               



### Action Outputs

| Name     | Description                | Default |
| -------- | -------------------------- | ------- |
| `None`   | This action does not provide outputs |         

A sample GitHub action that uses a chained functionality can be found in ```.github/workflows/test_chained_actions_sentinel_forward.yml```