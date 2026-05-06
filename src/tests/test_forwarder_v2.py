import sys

sys.path.append("../")
import json
from unittest.mock import patch, MagicMock
from azure.core.exceptions import HttpResponseError
from src.lib.forwarder_v2 import (
    handle_log,
    upload_data,
    convert_to_log_entries,
    process_file_to_entries,
    is_json,
)


# test is_json with valid json
def test_is_json_valid():
    assert is_json('{"foo": "bar"}') is True


# test is_json with invalid json
def test_is_json_invalid():
    assert is_json("not json") is False


# test convert_to_log_entries with a plain string
def test_convert_to_log_entries_string():
    result = convert_to_log_entries("foo message")
    assert result == [{"Message": "foo message"}]


# test convert_to_log_entries with a json object string
def test_convert_to_log_entries_json_object():
    result = convert_to_log_entries('{"key": "value"}')
    assert result == [{"key": "value"}]


# test convert_to_log_entries with a json array string
def test_convert_to_log_entries_json_array():
    result = convert_to_log_entries('[{"a": 1}, {"b": 2}]')
    assert result == [{"a": 1}, {"b": 2}]


# test process_file_to_entries with a text file
def test_process_file_to_entries_text():
    entries = process_file_to_entries("tests/data/test_file.txt")
    assert entries == [
        {"Message": "foo1"},
        {"Message": "foo2"},
        {"Message": "foo3"},
    ]


# test process_file_to_entries with a json file
def test_process_file_to_entries_json():
    entries = process_file_to_entries("tests/data/test_file.json")
    assert len(entries) == 1
    assert entries[0]["id1"] == "test data 1"


# test process_file_to_entries with a multiline json file
def test_process_file_to_entries_json_multiline():
    entries = process_file_to_entries("tests/data/test_file_muline.json")
    assert len(entries) == 1
    assert "id1" in entries[0]


# test process_file_to_entries with a latin encoded json file
def test_process_file_to_entries_json_latin():
    entries = process_file_to_entries("tests/data/test_file_latin.json")
    assert len(entries) == 1
    assert entries[0] == {"foo": "bar?baz"}


# test process_file_to_entries with a jsonl file
def test_process_file_to_entries_jsonl():
    entries = process_file_to_entries("tests/data/test_file.jsonl")
    assert len(entries) == 3
    assert entries[0]["id1"] == "test data 1"
    assert entries[1]["anotherid1"] == "test data for anotherid1"


# test upload_data success
def test_upload_data_success():
    mock_client = MagicMock()
    logs = [{"key": "value"}]
    result = upload_data(mock_client, "dcr-123", "Custom-Table", logs)
    assert result is True
    mock_client.upload.assert_called_once_with(
        rule_id="dcr-123", stream_name="Custom-Table", logs=logs
    )


# test upload_data failure
def test_upload_data_failure():
    mock_client = MagicMock()
    mock_client.upload.side_effect = HttpResponseError("Upload failed")
    logs = [{"key": "value"}]
    result = upload_data(mock_client, "dcr-123", "Custom-Table", logs)
    assert result is False


# test upload_data with empty logs
def test_upload_data_empty_logs():
    mock_client = MagicMock()
    result = upload_data(mock_client, "dcr-123", "Custom-Table", [])
    assert result is False
    mock_client.upload.assert_not_called()


# test handle_log with missing endpoint
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_missing_endpoint(mock_create_client):
    result = handle_log(
        file_name=False,
        input_data="foo",
        endpoint=False,
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is False
    mock_create_client.assert_not_called()


# test handle_log with missing dcr_rule_id
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_missing_dcr_rule_id(mock_create_client):
    result = handle_log(
        file_name=False,
        input_data="foo",
        endpoint="https://dce.example.com",
        dcr_rule_id=False,
        stream_name="Custom-Table",
    )
    assert result is False
    mock_create_client.assert_not_called()


# test handle_log with missing stream_name
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_missing_stream_name(mock_create_client):
    result = handle_log(
        file_name=False,
        input_data="foo",
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name=False,
    )
    assert result is False
    mock_create_client.assert_not_called()


# test handle_log with missing input_data and file_name
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_missing_input_and_file(mock_create_client):
    result = handle_log(
        file_name=False,
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is False
    mock_create_client.assert_not_called()


# test handle_log with input data string
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_input_data_string(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name=False,
        input_data="foo message",
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    mock_client.upload.assert_called_once_with(
        rule_id="dcr-123",
        stream_name="Custom-Table",
        logs=[{"Message": "foo message"}],
    )


# test handle_log with input data json
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_input_data_json(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name=False,
        input_data=json.dumps({"Message": "foo message"}),
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    mock_client.upload.assert_called_once_with(
        rule_id="dcr-123",
        stream_name="Custom-Table",
        logs=[{"Message": "foo message"}],
    )


# test handle_log with text file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_text_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file.txt",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    assert len(logs) == 3
    assert logs[0] == {"Message": "foo1"}


# test handle_log with json file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_json_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file.json",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    assert len(logs) == 1
    assert logs[0]["id1"] == "test data 1"


# test handle_log with jsonl file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_jsonl_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file.jsonl",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    assert len(logs) == 3


# test handle_log with multiline json file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_multiline_json_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file_muline.json",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    assert len(logs) == 1


# test handle_log with latin encoded json file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_latin_json_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file_latin.json",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    assert len(logs) == 1
    assert logs[0] == {"foo": "bar?baz"}


# test handle_log with both input data and file
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_input_data_and_file(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="tests/data/test_file.txt",
        input_data="extra message",
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is True
    call_args = mock_client.upload.call_args
    logs = call_args.kwargs["logs"]
    # 1 from input_data + 3 from file
    assert len(logs) == 4
    assert logs[0] == {"Message": "extra message"}


# test handle_log with file that does not exist
@patch("src.lib.forwarder_v2.create_client")
def test_handle_log_file_does_not_exist(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    result = handle_log(
        file_name="file_that_does_not_exist.txt",
        input_data=False,
        endpoint="https://dce.example.com",
        dcr_rule_id="dcr-123",
        stream_name="Custom-Table",
    )
    assert result is False
