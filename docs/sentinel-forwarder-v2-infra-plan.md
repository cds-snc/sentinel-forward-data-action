# Sentinel Repo — Forwarder v2 Infrastructure Plan

> **Purpose:** Create all Azure infrastructure in `cds-snc/sentinel` to support migrating
> GitHub Actions workflows from the v1 Data Collector API to the v2 Logs Ingestion API
> via `cds-snc/sentinel-forward-data-action`.

---

## Architecture Overview

```
GitHub Actions workflow
  │
  └─ sentinel-forward-data-action (v2)
       │
       ├─ AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET (org secrets)
       │    └─► DefaultAzureCredential ──► Azure AD App Registration
       │
       ├─ DCE (Data Collection Endpoint) ◄── shared, one for all tables
       │
       └─ DCR (Data Collection Rule) ◄── one per log type / custom table
            │
            └─ Custom Table in Log Analytics Workspace
```

---

## Step 1 — App Registration + Client Secret

Create a dedicated App Registration with a client secret for the forwarder v2.
Using a client secret instead of OIDC federated credentials avoids the
**20 federated credentials per app registration limit** — important since 74+
repos will use this action.

### Terraform resources

```hcl
# App Registration
resource "azuread_application" "sentinel_forwarder_v2" {
  display_name = "sentinel-forwarder-v2-github-actions"
}

resource "azuread_service_principal" "sentinel_forwarder_v2" {
  client_id = azuread_application.sentinel_forwarder_v2.client_id
}

# Client secret (rotate periodically — set end_date_relative or end_date)
resource "azuread_application_password" "sentinel_forwarder_v2" {
  application_id    = azuread_application.sentinel_forwarder_v2.id
  display_name      = "sentinel-forwarder-v2-github-actions-secret"
  end_date_relative = "8760h"  # 1 year — adjust to your rotation policy
}
```

### Outputs needed

| Value | Where to store |
|-------|---------------|
| `azuread_application.sentinel_forwarder_v2.client_id` | Org secret `SENTINEL_V2_AZURE_CLIENT_ID` |
| `azuread_application_password.sentinel_forwarder_v2.value` | Org secret `SENTINEL_V2_AZURE_CLIENT_SECRET` |
| Azure AD tenant ID | Org secret `SENTINEL_V2_AZURE_TENANT_ID` |

> **Secret rotation:** Set a calendar reminder to rotate `SENTINEL_V2_AZURE_CLIENT_SECRET`
> before it expires. You can create a second password resource before the first expires
> to allow a zero-downtime rotation.

---

## Step 2 — Data Collection Endpoint (DCE)

One shared DCE for all forwarder v2 ingestion.

### Terraform resource

```hcl
resource "azurerm_monitor_data_collection_endpoint" "sentinel_forwarder" {
  name                          = "dce-sentinel-forwarder-v2"
  resource_group_name           = var.resource_group_name     # same RG as LAW
  location                      = var.location                 # same region as LAW
  kind                          = "Linux"                      # or omit for default
  public_network_access_enabled = true                         # GitHub Actions needs public access
}
```

### Outputs needed

| Value | Where to store |
|-------|---------------|
| `azurerm_monitor_data_collection_endpoint.sentinel_forwarder.logs_ingestion_endpoint` | Org secret `SENTINEL_DCE_ENDPOINT` |

---

## Step 3 — Custom Tables + Data Collection Rules (DCRs)

Each log type needs:
1. A custom table in the Log Analytics Workspace (defines the schema)
2. A DCR (defines the stream → table mapping + optional transform)

### Complete list of DCRs to create

| # | Log Type (v1 `log_type`) | Custom Table Name | Stream Name | Priority | Used by |
|---|--------------------------|-------------------|-------------|----------|---------|
| 1 | `GitHubMetadata_OSSF_Scorecard` | `GitHubMetadata_OSSF_Scorecard_CL` | `Custom-GitHubMetadata_OSSF_Scorecard_CL` | **Phase 1** | ~74 repos |
| 2 | `CDS_Product_Deployment_Data` | `CDS_Product_Deployment_Data_CL` | `Custom-CDS_Product_Deployment_Data_CL` | Phase 2 | 14 repos |
| 3 | `CDS_OWASPZap_Results` | `CDS_OWASPZap_Results_CL` | `Custom-CDS_OWASPZap_Results_CL` | Phase 3 | automatic-website-scanning |
| 4 | `CDS_A11ywatch_Results` | `CDS_A11ywatch_Results_CL` | `Custom-CDS_A11ywatch_Results_CL` | Phase 3 | automatic-website-scanning |
| 5 | `CDS_Nuclei_Results` | `CDS_Nuclei_Results_CL` | `Custom-CDS_Nuclei_Results_CL` | Phase 3 | automatic-website-scanning |
| 6 | `CDS_Lighthouse_Results` | `CDS_Lighthouse_Results_CL` | `Custom-CDS_Lighthouse_Results_CL` | Phase 3 | automatic-website-scanning |
| 7 | `CDS_Vulnerability_Report_Data` | `CDS_Vulnerability_Report_Data_CL` | `Custom-CDS_Vulnerability_Report_Data_CL` | Phase 3 | site-reliability-engineering |

> `TestData` (dns-proxy-action) is for testing only — skip or create last.

### Reusable Terraform module pattern

Since all DCRs follow the same structure, create a reusable module:

```hcl
# modules/dcr_custom_table/variables.tf

variable "name" {
  description = "Short name for the DCR (e.g. 'ossf-scorecard')"
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics Workspace"
  type        = string
}

variable "data_collection_endpoint_id" {
  description = "Resource ID of the shared DCE"
  type        = string
}

variable "table_name" {
  description = "Custom table name without _CL suffix (e.g. 'GitHubMetadata_OSSF_Scorecard')"
  type        = string
}

variable "columns" {
  description = "List of column definitions for the custom table"
  type = list(object({
    name = string
    type = string  # string, int, long, real, bool, datetime, dynamic
  }))
}

variable "transform_kql" {
  description = "Optional KQL transform. Use 'source' for passthrough."
  type        = string
  default     = "source"
}
```

```hcl
# modules/dcr_custom_table/main.tf

resource "azurerm_log_analytics_workspace_table" "this" {
  workspace_id = var.log_analytics_workspace_id
  name         = "${var.table_name}_CL"

  plan = "Analytics"

  column {
    name = "TimeGenerated"
    type = "datetime"
  }

  dynamic "column" {
    for_each = var.columns
    content {
      name = column.value.name
      type = column.value.type
    }
  }
}

resource "azurerm_monitor_data_collection_rule" "this" {
  name                        = "dcr-${var.name}"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = var.data_collection_endpoint_id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "la-destination"
    }
  }

  data_flow {
    streams       = ["Custom-${var.table_name}_CL"]
    destinations  = ["la-destination"]
    transform_kql = var.transform_kql
    output_stream = "Custom-${var.table_name}_CL"
  }

  stream_declaration {
    stream_name = "Custom-${var.table_name}_CL"

    dynamic "column" {
      for_each = concat(
        [{ name = "TimeGenerated", type = "datetime" }],
        var.columns
      )
      content {
        name = column.value.name
        type = column.value.type
      }
    }
  }
}
```

```hcl
# modules/dcr_custom_table/outputs.tf

output "dcr_immutable_id" {
  description = "The immutable ID of the DCR (used as dcr_rule_id in the action)"
  value       = azurerm_monitor_data_collection_rule.this.immutable_id
}

output "dcr_id" {
  description = "The Azure resource ID of the DCR (used for role assignments)"
  value       = azurerm_monitor_data_collection_rule.this.id
}

output "stream_name" {
  value = "Custom-${var.table_name}_CL"
}

output "table_name" {
  value = "${var.table_name}_CL"
}
```

### Phase 1 — OSSF Scorecard DCR

```hcl
module "dcr_ossf_scorecard" {
  source = "./modules/dcr_custom_table"

  name                        = "ossf-scorecard"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  log_analytics_workspace_id  = azurerm_log_analytics_workspace.sentinel.id
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.sentinel_forwarder.id
  table_name                  = "GitHubMetadata_OSSF_Scorecard"

  # Columns based on OSSF scorecard JSON output + metadata fields.
  # Adjust types to match the actual schema from ossf/scorecard-action output.
  columns = [
    { name = "date",             type = "string" },
    { name = "repo",             type = "dynamic" },
    { name = "scorecard",        type = "dynamic" },
    { name = "score",            type = "real" },
    { name = "checks",           type = "dynamic" },
    { name = "metadata",         type = "dynamic" },
    { name = "metadata_owner",   type = "string" },
    { name = "metadata_repo",    type = "string" },
    { name = "metadata_query",   type = "string" },
  ]
}
```

### Phase 2 — Deployment Data DCR

```hcl
module "dcr_deployment_data" {
  source = "./modules/dcr_custom_table"

  name                        = "product-deployment"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  log_analytics_workspace_id  = azurerm_log_analytics_workspace.sentinel.id
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.sentinel_forwarder.id
  table_name                  = "CDS_Product_Deployment_Data"

  columns = [
    { name = "product",     type = "string" },
    { name = "sha",         type = "string" },
    { name = "version",     type = "string" },
    { name = "repository",  type = "string" },
    { name = "environment", type = "string" },
    { name = "status",      type = "string" },
  ]
}
```

### Phase 3 — Scanning & Vulnerability DCRs

```hcl
# Add similar module calls for each:
# - CDS_OWASPZap_Results
# - CDS_A11ywatch_Results
# - CDS_Nuclei_Results
# - CDS_Lighthouse_Results
# - CDS_Vulnerability_Report_Data
#
# Column schemas will need to be derived from the actual data each tool produces.
# Tip: query the existing v1 tables in LAW to get the current schema:
#   TableName_CL | getschema
```

---

## Step 4 — Role Assignments

Grant the app registration **Monitoring Metrics Publisher** on each DCR.

```hcl
locals {
  dcr_ids = [
    module.dcr_ossf_scorecard.dcr_id,
    module.dcr_deployment_data.dcr_id,
    # ... add more as created
  ]
}

resource "azurerm_role_assignment" "forwarder_v2_metrics_publisher" {
  for_each = toset(local.dcr_ids)

  scope                = each.value
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azuread_service_principal.sentinel_forwarder_v2.object_id
}
```

---

## Step 5 — GitHub Org Secrets

After `terraform apply`, set these org-level secrets in `cds-snc`:

| Secret name | Source |
|-------------|--------|
| `SENTINEL_V2_AZURE_CLIENT_ID` | `azuread_application.sentinel_forwarder_v2.client_id` |
| `SENTINEL_V2_AZURE_CLIENT_SECRET` | `azuread_application_password.sentinel_forwarder_v2.value` |
| `SENTINEL_V2_AZURE_TENANT_ID` | Azure AD tenant ID |
| `SENTINEL_DCE_ENDPOINT` | `azurerm_monitor_data_collection_endpoint.sentinel_forwarder.logs_ingestion_endpoint` |
| `SENTINEL_DCR_RULE_ID_OSSF` | `module.dcr_ossf_scorecard.dcr_immutable_id` |
| `SENTINEL_STREAM_NAME_OSSF` | `Custom-GitHubMetadata_OSSF_Scorecard_CL` |
| `SENTINEL_DCR_RULE_ID_DEPLOYMENT` | `module.dcr_deployment_data.dcr_immutable_id` |
| `SENTINEL_STREAM_NAME_DEPLOYMENT` | `Custom-CDS_Product_Deployment_Data_CL` |
| *(add more per DCR as they are created)* | |

> **Tip:** Consider using Terraform + GitHub provider to manage org secrets directly,
> or output the values and set them manually / via `gh secret set`.

---

## Execution Checklist

### Phase 1 — OSSF Scorecard (do first)
- [ ] Create app registration + service principal + client secret
- [ ] Create DCE
- [ ] Create custom table + DCR for `GitHubMetadata_OSSF_Scorecard`
- [ ] Add role assignment (Monitoring Metrics Publisher on DCR)
- [ ] `terraform plan` → review
- [ ] `terraform apply`
- [ ] Set org secrets in GitHub
- [ ] Test: update `sentinel-forward-data-action` own `ossf-scorecard.yml` to v2
- [ ] Validate: query `GitHubMetadata_OSSF_Scorecard_CL` in LAW for new v2 records
- [ ] Pilot: convert 1-2 more repos (e.g. `cds-azure-resources`)
- [ ] Rollout: batch-convert remaining OSSF repos

### Phase 2 — Deployment Data
- [ ] Create custom table + DCR for `CDS_Product_Deployment_Data`
- [ ] Add role assignment
- [ ] `terraform apply`
- [ ] Set org secrets (`SENTINEL_DCR_RULE_ID_DEPLOYMENT`, `SENTINEL_STREAM_NAME_DEPLOYMENT`)
- [ ] Convert deployment workflows in 14 repos

### Phase 3 — Scanning & Vulnerability
- [ ] Create custom tables + DCRs for remaining 5 log types
- [ ] Add role assignments
- [ ] `terraform apply`
- [ ] Set secrets and convert `automatic-website-scanning` + `site-reliability-engineering`

### Cleanup
- [ ] Remove old v1 org secrets (`LOG_ANALYTICS_WORKSPACE_ID`, `LOG_ANALYTICS_WORKSPACE_KEY`) once all repos migrated
- [ ] Consider deprecating v1 code path in the action

---

## Important Notes

1. **Client secret auth** is used instead of OIDC federated credentials. Azure AD limits federated credentials to **20 per app registration** (confirmed [May 2026](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-considerations)), which is insufficient for 74+ repos. A single client secret works across all repos via org-level GitHub secrets with no per-repo setup.

2. **Rotate the client secret** before it expires. Set `end_date_relative` in Terraform and a calendar reminder. For zero-downtime rotation, create a new password before deleting the old one.

3. **Custom table schemas must match the incoming data.** For OSSF, the scorecard JSON has nested objects — use `dynamic` type for those columns. Query existing v1 tables (`TableName_CL | getschema`) to derive schemas for other log types.

4. **The DCE must be in the same region as the Log Analytics Workspace.**

5. **`stream_declaration` columns must match table columns exactly** — including `TimeGenerated`. If the incoming data doesn't have `TimeGenerated`, use a KQL transform: `source | extend TimeGenerated = now()`.

6. **Monitoring Metrics Publisher** is the minimum role needed. Don't use Contributor or broader roles.
