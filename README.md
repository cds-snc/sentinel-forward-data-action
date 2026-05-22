# Send data to Azure Sentinel Github-action

A GitHub action that sends data to Azure Sentinel from a previous GitHub action. It can either take as inputs a file name or input data that is either plain text or json format. Data will be stored in the specified custom table.

This action supports two APIs:

- **v2 (Logs Ingestion API)** — recommended for new setups. Uses OIDC federated credentials and Data Collection Rules.
- **v1 (Data Collector API)** — legacy. Uses workspace ID and shared key.

---

## v2 Usage (Logs Ingestion API)

The action performs its own GitHub Actions OIDC token exchange internally — no separate `azure/login` step is needed.

> **Required:** the calling workflow must grant `id-token: write` permission. Without it, the GitHub OIDC token request env vars are not injected into the action's container and authentication will fail with `DefaultAzureCredential failed to retrieve a token`.

```yaml
permissions:
  id-token: write  # required for OIDC federated credentials

steps:
  - name: "Post results to Sentinel"
    uses: cds-snc/sentinel-forward-data-action@main
    with:
      file_name: ossf-results-modified.json
      dce_endpoint: ${{ secrets.SENTINEL_DCE_ENDPOINT }}
      dcr_rule_id: ${{ secrets.SENTINEL_DCR_RULE_ID_OSSF }}
      stream_name: ${{ secrets.SENTINEL_STREAM_NAME_OSSF }}
      azure_client_id: ${{ secrets.SENTINEL_V2_AZURE_CLIENT_ID }}
      azure_tenant_id: ${{ secrets.SENTINEL_V2_AZURE_TENANT_ID }}
```

### v2 Inputs

| Name                  | Description                                                            | Required                                 |
| --------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| `file_name`           | File to read and send to Sentinel (text or json format)                | No (provide `file_name` or `input_data`) |
| `input_data`          | Inline data to send to Sentinel (text or json format)                  | No (provide `file_name` or `input_data`) |
| `dce_endpoint`        | The Data Collection Endpoint (DCE) URL                                 | Yes                                      |
| `dcr_rule_id`         | The immutable ID of the Data Collection Rule (DCR)                     | Yes                                      |
| `stream_name`         | The stream name in the DCR (e.g. `Custom-MyTable_CL`)                  | Yes                                      |
| `azure_client_id`     | The Azure AD application (client) ID                                   | Yes                                      |
| `azure_tenant_id`     | The Azure AD tenant ID                                                 | Yes                                      |
| `azure_client_secret` | Azure AD client secret (omit to use GitHub OIDC federated credentials) | No                                       |

---

## v1 Usage (Data Collector API — Legacy)

```yaml
steps:
  - name: "Post results to Sentinel"
    uses: cds-snc/sentinel-forward-data-action@main
    with:
      file_name: file-name.json
      input_data: "Data to be sent to Sentinel"
      log_type: "TestData"
      log_analytics_workspace_id: ${{ secrets.LOG_ANALYTICS_WORKSPACE_ID }}
      log_analytics_workspace_key: ${{ secrets.LOG_ANALYTICS_WORKSPACE_KEY }}
```

### v1 Inputs

| Name                          | Description                                             | Required                                 |
| ----------------------------- | ------------------------------------------------------- | ---------------------------------------- |
| `file_name`                   | File to read and send to Sentinel (text or json format) | No (provide `file_name` or `input_data`) |
| `input_data`                  | Inline data to send to Sentinel (text or json format)   | No (provide `file_name` or `input_data`) |
| `log_type`                    | The custom log table name (without the `_CL` suffix)    | Yes                                      |
| `log_analytics_workspace_id`  | Sentinel workspace ID                                   | Yes                                      |
| `log_analytics_workspace_key` | Sentinel workspace shared key                           | Yes                                      |

---

### Action Outputs

| Name   | Description                          | Default |
| ------ | ------------------------------------ | ------- |
| `None` | This action does not provide outputs |         |

A sample GitHub action that uses a chained functionality can be found in `.github/workflows/test_chained_actions_sentinel_forward.yml`
