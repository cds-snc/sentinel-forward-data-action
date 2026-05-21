# Forwarder v2 Infrastructure Plan

> **Purpose:** Create all Azure infrastructure to support migrating
> GitHub Actions workflows from the v1 Data Collector API to the v2 Logs Ingestion API
> via `cds-snc/sentinel-forward-data-action`.
>
> Infrastructure is split across two repos:
> - **`cds-snc/cds-azure-resources`** — App Registration (Azure AD)
> - **`cds-snc/sentinel`** — DCE, DCRs, custom tables, and role assignments

---

## Architecture Overview

```
GitHub Actions workflow (any cds-snc repo)
  │
  ├─ azure/login (OIDC) ──► Azure AD App Registration
  │    └─ Flexible Federated Identity Credential (preview)
  │       subject matches 'repo:cds-snc/*'  ← one credential covers all repos
  │
  └─ sentinel-forward-data-action (v2)
       │
       └─ DefaultAzureCredential (picks up OIDC token from azure/login)
            │
            ├─ DCE (Data Collection Endpoint) ◄── shared, one for all tables
            │       (managed in sentinel repo)
            │
            └─ DCR (Data Collection Rule) ◄── one per log type / custom table
                 │   (managed in sentinel repo)
                 │   (Monitoring Metrics Publisher role granted here)
                 │
                 └─ Custom Table in Log Analytics Workspace
```

---

# Part 1 — `cds-snc/cds-azure-resources` repo

This repo manages Azure AD resources only.

## Step 1 — App Registration + Flexible Federated Identity Credential

Create a dedicated App Registration with a **single flexible federated identity
credential** that covers all `cds-snc` repos using a wildcard `matches` expression.
This avoids the 20 federated credentials per app limit.

### Terraform resources

```hcl
# App Registration
resource "azuread_application_registration" "sentinel_forwarder_v2" {
  display_name = "sentinel-forwarder-v2-github-actions"
}

resource "azuread_service_principal" "sentinel_forwarder_v2" {
  client_id = azuread_application_registration.sentinel_forwarder_v2.client_id
}

# Flexible Federated Identity Credential — one credential covers all cds-snc repos
resource "azuread_application_flexible_federated_identity_credential" "github_oidc" {
  application_id             = azuread_application_registration.sentinel_forwarder_v2.id
  display_name               = "github-actions-cds-snc-all-repos"
  description                = "OIDC for sentinel-forward-data-action across all cds-snc repos"
  audience                   = "api://AzureADTokenExchange"
  issuer                     = "https://token.actions.githubusercontent.com"
  claims_matching_expression = "claims['sub'] matches 'repo:cds-snc/*'"
}
```

### Outputs needed

| Value | Where to store |
|-------|---------------|
| `azuread_application_registration.sentinel_forwarder_v2.client_id` | Org secret `SENTINEL_V2_AZURE_CLIENT_ID` |
| Azure AD tenant ID | Org secret `SENTINEL_V2_AZURE_TENANT_ID` |
| Subscription ID (of the LAW) | Org secret `SENTINEL_V2_AZURE_SUBSCRIPTION_ID` |
| `azuread_service_principal.sentinel_forwarder_v2.object_id` | Needed by `sentinel` repo for role assignments |

---

# Part 2 — `cds-snc/sentinel` repo

This repo manages the DCE, DCRs, custom tables, and role assignments.

---

## Step 2 — Data Collection Endpoint (DCE)

One shared DCE for all forwarder v2 ingestion.

### Terraform resource

```hcl
resource "azurerm_monitor_data_collection_endpoint" "sentinel_forwarder" {
  name                          = "dce-sentinel-forwarder-v2"
  resource_group_name           = var.resource_group_name     # same RG as LAW
  location                      = var.location                 # same region as LAW
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

Grant the app registration **Monitoring Metrics Publisher** on each **DCR**.
No role assignment is needed on the DCE — the DCE is just the ingestion endpoint URL;
authorization is checked at the DCR level.

The service principal object ID comes from the `cds-azure-resources` repo output
(or a data source / variable).

```hcl
variable "sentinel_forwarder_v2_principal_id" {
  description = "Object ID of the sentinel-forwarder-v2 service principal (from cds-azure-resources)"
  type        = string
}

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
  principal_id         = var.sentinel_forwarder_v2_principal_id
}
```

---

## Step 5 — GitHub Org Secrets

After `terraform apply`, set these org-level secrets in `cds-snc`:

| Secret name | Source | Set after |
|-------------|--------|----------|
| `SENTINEL_V2_AZURE_CLIENT_ID` | App registration client ID | `cds-azure-resources` apply |
| `SENTINEL_V2_AZURE_TENANT_ID` | Azure AD tenant ID | `cds-azure-resources` apply |
| `SENTINEL_V2_AZURE_SUBSCRIPTION_ID` | Subscription ID | `cds-azure-resources` apply |
| `SENTINEL_DCE_ENDPOINT` | DCE logs ingestion endpoint | `sentinel` apply |
| `SENTINEL_DCR_RULE_ID_OSSF` | `module.dcr_ossf_scorecard.dcr_immutable_id` | `sentinel` apply |
| `SENTINEL_STREAM_NAME_OSSF` | `Custom-GitHubMetadata_OSSF_Scorecard_CL` | `sentinel` apply |
| `SENTINEL_DCR_RULE_ID_DEPLOYMENT` | `module.dcr_deployment_data.dcr_immutable_id` | `sentinel` apply |
| `SENTINEL_STREAM_NAME_DEPLOYMENT` | `Custom-CDS_Product_Deployment_Data_CL` | `sentinel` apply |
| *(add more per DCR as they are created)* | | |

> **Tip:** Consider using Terraform + GitHub provider to manage org secrets directly,
> or output the values and set them manually / via `gh secret set`.

---

## Execution Checklist

### Phase 1 — OSSF Scorecard (do first)

**`cds-azure-resources` repo:**
- [ ] Create app registration + service principal
- [ ] Create flexible federated identity credential (`claims['sub'] matches 'repo:cds-snc/*'`)
- [ ] `terraform plan` → review
- [ ] `terraform apply`
- [ ] Set org secrets: `SENTINEL_V2_AZURE_CLIENT_ID`, `SENTINEL_V2_AZURE_TENANT_ID`, `SENTINEL_V2_AZURE_SUBSCRIPTION_ID`

**`sentinel` repo:**
- [ ] Create DCE
- [ ] Create custom table + DCR for `GitHubMetadata_OSSF_Scorecard`
- [ ] Add role assignment (Monitoring Metrics Publisher on DCR)
- [ ] `terraform plan` → review
- [ ] `terraform apply`
- [ ] Set org secrets: `SENTINEL_DCE_ENDPOINT`, `SENTINEL_DCR_RULE_ID_OSSF`, `SENTINEL_STREAM_NAME_OSSF`

**Validation:**
- [ ] Test: update `sentinel-forward-data-action` own `ossf-scorecard.yml` to v2
- [ ] Validate: query `GitHubMetadata_OSSF_Scorecard_CL` in LAW for new v2 records
- [ ] Pilot: convert 1-2 more repos (e.g. `cds-azure-resources`)
- [ ] Rollout: batch-convert remaining OSSF repos

### Phase 2 — Deployment Data
- [ ] (`sentinel` repo) Create custom table + DCR for `CDS_Product_Deployment_Data`
- [ ] (`sentinel` repo) Add role assignment
- [ ] `terraform apply`
- [ ] Set org secrets (`SENTINEL_DCR_RULE_ID_DEPLOYMENT`, `SENTINEL_STREAM_NAME_DEPLOYMENT`)
- [ ] Convert deployment workflows in 14 repos

### Phase 3 — Scanning & Vulnerability
- [ ] (`sentinel` repo) Create custom tables + DCRs for remaining 5 log types
- [ ] (`sentinel` repo) Add role assignments
- [ ] `terraform apply`
- [ ] Set secrets and convert `automatic-website-scanning` + `site-reliability-engineering`

### Cleanup
- [ ] Remove old v1 org secrets (`LOG_ANALYTICS_WORKSPACE_ID`, `LOG_ANALYTICS_WORKSPACE_KEY`) once all repos migrated
- [ ] Consider deprecating v1 code path in the action

---

## Important Notes

1. **OIDC with Flexible Federated Identity Credentials.** A single `azuread_application_flexible_federated_identity_credential` with `claims['sub'] matches 'repo:cds-snc/*'` covers all repos in the org — no 20-credential limit issue, no client secret rotation. See [Terraform docs](https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/application_flexible_federated_identity_credential) and [Microsoft docs](https://learn.microsoft.com/en-us/entra/workload-id/workload-identities-flexible-federated-identity-credentials?tabs=github).

2. **Permissions are on the DCR, not the DCE.** The DCE is just the ingestion endpoint URL. Authorization is checked at the DCR level via the **Monitoring Metrics Publisher** role.

3. **Infrastructure is split across two repos:**
   - `cds-azure-resources` — App Registration, flexible FIC (Azure AD only)
   - `sentinel` — DCE, DCRs, custom tables, role assignments (all monitoring infra)

4. **Custom table schemas must match the incoming data.** For OSSF, the scorecard JSON has nested objects — use `dynamic` type for those columns. Query existing v1 tables (`TableName_CL | getschema`) to derive schemas for other log types.

5. **The DCE must be in the same region as the Log Analytics Workspace.**

6. **`stream_declaration` columns must match table columns exactly** — including `TimeGenerated`. If the incoming data doesn't have `TimeGenerated`, use a KQL transform: `source | extend TimeGenerated = now()`.

7. **Monitoring Metrics Publisher** is the minimum role needed. Don't use Contributor or broader roles.
