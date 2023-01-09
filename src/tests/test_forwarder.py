import sys
import pytest
import json
from unittest.mock import patch
sys.path.append("../")
from src.lib.forwarder import handle_log, build_signature, post_data


# test with both input data and file name not provided
def test_handle_log_input_file_and_input_data_not_provided():
    assert handle_log(file_name=False, input_data=False, log_analytics_workspace_id="foo", log_analytics_workspace_key="foo", log_type="foo") is False
    
# test with log_analytics_workspace_id_not_provided    
def test_handle_log_log_analytics_workspace_id_not_provided():
    assert handle_log(file_name="foo.txt", input_data="foo", log_analytics_workspace_id=False, log_analytics_workspace_key="foo", log_type="foo") is False
    
# test with log_analytics_workspace_key_not_provided       
def test_handle_log_log_analytics_workspace_key_not_provided():
    assert handle_log(file_name="foo.txt", input_data="foo", log_analytics_workspace_id="foo", log_analytics_workspace_key=False, log_type="foo") is False
  
# test with log_type not provided  
def test_handle_log_log_type_not_provided():
    assert handle_log(file_name="foo.txt", input_data="foo", log_analytics_workspace_id="foo", log_analytics_workspace_key="foo", log_type=False) is False

# test input file does not exist
def test_handle_log_input_file_does_not_exist():
    assert handle_log(file_name="file_that_does_not_exist.txt", input_data=False, log_analytics_workspace_id="foo", log_analytics_workspace_key="bGBavCBrZXr=", log_type="foo") is False
    
# test with input data as string
@patch("src.lib.forwarder.post_data")
def test_handle_log_succeeds_with_input_data_string(mock_post_data):
    mock_post_data.return_value = True
    assert handle_log(file_name=False, input_data="foo message", log_analytics_workspace_id="foo", log_analytics_workspace_key="bGBavCBrZXr=", log_type="foo") is True
    assert mock_post_data.call_count == 1


# test with input data as json object 
@patch("src.lib.forwarder.post_data")
def test_handle_log_succeeds_with_input_data_json(mock_post_data):
    mock_post_data.return_value = True
    assert handle_log(file_name=False, input_data=json.dumps({"Message":"foo message"}), log_analytics_workspace_id="foo", log_analytics_workspace_key="bGBavCBrZXr=", log_type="foo") is True
    assert mock_post_data.call_count == 1
     
   
# test with reading input from file 
@patch("src.lib.forwarder.post_data")
def test_handle_log_input_file_provided(mock_post_data):
    mock_post_data.return_value = True
    assert handle_log(file_name="tests/data/test_file.txt", input_data=False, log_analytics_workspace_id="foo", log_analytics_workspace_key="bGBavCBrZXr=", log_type="foo") is True
    # assert that the number of post_data calls are equal to the number of lines in the test file
    assert mock_post_data.call_count == sum(1 for _ in open("tests/data/test_file.txt"))

# test with reading input from file plus sending input data
@patch("src.lib.forwarder.post_data")
def test_handle_log_input_file_provided(mock_post_data):
    mock_post_data.return_value = True
    assert handle_log(file_name="tests/data/test_file.txt", input_data="foo", log_analytics_workspace_id="foo", log_analytics_workspace_key="bGBavCBrZXr=", log_type="foo") is True
    # assert that the number of post_data calls are equal to the number of lines in the test file
    assert mock_post_data.call_count == (sum(1 for _ in open("tests/data/test_file.txt")) + 1)
    
# test build signature function    
def test_build_signature():
    body = "{}"
    method = "POST"
    content_type = "application/json"
    resource = "/api/logs"
    date = "Sun, 21 Nov 2021 18:35:52 GMT"
    content_length = len(body)

    expected = "SharedKey log_analytics_workspace_id:OWBEzzhtD2AVHvc02xvhKGDbj9dR65YlVvdESfqQ8Eg="
    assert (
        build_signature(
            "log_analytics_workspace_id",
            "bGBavCBrZXr=",
            date,
            content_length,
            method,
            content_type,
            resource,
        )
        == expected
    )

# test successful execution of post_data function
@patch("src.lib.forwarder.requests")
def test_post_data_success(mock_requests):
    mock_requests.post.return_value.status_code = 200
    assert post_data(log_analytics_workspace_id = "foo", log_analytics_workspace_key = "bGBavCBrZXr=", body = {}, log_type = "foo")

# test unsuccessful exectuion of post_data function
@patch("src.lib.forwarder.requests")
def test_post_data_failure(mock_requests):
    mock_requests.post.return_value.status_code = 400
    assert post_data(log_analytics_workspace_id = "foo", log_analytics_workspace_key = "bGBavCBrZXr=", body = {}, log_type = "foo") is False