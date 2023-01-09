# Send data to Sentinel from a previous github action or from contents of a file 

This Github action takes data from a previous github action passed in as input_data and send it to Sentinel. If  a file_name is provided as as input, then the Github action reads the contents of each file and sends it to Sentinel.

To use this in your github action, pass in the outputs of your github action to this one. You can see a sample github action that uses this chained functionality in .github/workflows/test_chained_actions_sentinel_forward.yml