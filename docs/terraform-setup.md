# Terraform Setup for Logs Ingestion API (v2)

This guide shows how to provision the Azure infrastructure needed to use the v2 (Logs Ingestion API) path of this action using Terraform.

## Key Concept: Data Collector API Type Suffixes

The old Data Collector API (v1) automatically:
1. **Appends type suffixes** to column names based on detected value types:
   - `_s` → string
   - `_d` → double/number
   - `_b` → boolean
   - `_t` → datetime
   - `_g` → GUID
2. **Flattens nested objects** into `parent_child_s` format (e.g., `{"details": {"env": "prod"}}` → column `details_env_s`)

**Your existing tables already have these suffixed column names.** The new Logs Ingestion API does NOT do this automatically — but we can use DCR transformations (KQL) to handle the renaming and flattening, so **your JSON data stays exactly the same**.

## Architecture Overview

```
GitHub Actions workflow
  │
  ├─ azure/login (OIDC) → Entra app with federated credential
  │
  └─ sentinel-forward-data-action
       │
       └─ LogsIngestionClient.upload()  ← sends raw JSON (no suffixes)
            │
            ├─ DCE (Data Collection Endpoint)
            ├─ DCR (Data Collection Rule)
            │    └─ transform_kql: renames fields + adds suffixes + flattens objects
            └─ Log Analytics table (existing, with _s/_d/_b columns)
```

## Prerequisites

- Terraform >= 1.3
- Azure subscription with a Log Analytics workspace
- `azurerm` provider >= 3.80 (for `azurerm_monitor_data_collection_rule` with `stream_declaration`)

## Provider Configuration

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.80.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = ">= 2.47.0"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {}
```

## Variables

```hcl
variable "resource_group_name" {
  description = "Name of the resource group containing the Log Analytics workspace"
  type        = string
}

variable "location" {
  description = "Azure region (must match the Log Analytics workspace region)"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace"
  type        = string
}

variable "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  type        = string
}

variable "github_org" {
  description = "GitHub organization name for OIDC federation"
  type        = string
  default     = "cds-snc"
}

variable "github_repo" {
  description = "GitHub repository name for OIDC federation (e.g. 'my-app')"
  type        = string
}

variable "table_name" {
  description = "Custom log table name without _CL suffix (e.g. 'CdsDeployments')"
  type        = string
}
```

## Data Collection Endpoint (DCE)

One DCE can be shared across multiple DCRs in the same region.

```hcl
resource "azurerm_monitor_data_collection_endpoint" "this" {
  name                          = "dce-sentinel-forwarder"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  public_network_access_enabled = true

  lifecycle {
    create_before_destroy = true
  }
}
```

## Discovering Your Existing Table Schema

Before creating the DCR, you need to know what columns your existing table has. The old Data Collector API created these columns with type suffixes automatically.

### Option 1: Query the table schema via Azure CLI

```bash
az monitor log-analytics workspace table show \
  --resource-group rg-sentinel \
  --workspace-name law-sentinel \
  --name CdsDeployments_CL \
  --query "schema.columns[?!starts_with(name, '_')].{name: name, type: type}" \
  --output table
```

Example output:
```
Name               Type
-----------------  --------
TimeGenerated      datetime
product_s          string
sha_s              string
repository_s       string
environment_s      string
details_env_s      string    ← flattened from {"details": {"env": "..."}}
details_region_s   string    ← flattened from {"details": {"region": "..."}}
count_d            real      ← number type gets _d suffix
enabled_b          boolean   ← boolean type gets _b suffix
```

### Option 2: Query via KQL

```kql
CdsDeployments_CL
| getschema
| where ColumnName !startswith "_" and ColumnName != "TenantId" and ColumnName != "Type"
| project ColumnName, ColumnType
```

### Understanding the suffix mapping

| JSON value type | Suffix added by old API | Log Analytics column type |
|---|---|---|
| String | `_s` | `string` |
| Number (float/int) | `_d` | `real` |
| Boolean | `_b` | `boolean` |
| ISO 8601 datetime string | `_t` | `datetime` |
| GUID string | `_g` | `string` |
| Nested object | flattened: `parent_child_s` | `string` (each leaf) |
| Array | `_s` (JSON-serialized) | `string` |

## Migrating Existing Tables

Tables created by the old Data Collector API must be migrated before they can be used with a DCR. This is a one-time, idempotent operation that preserves all existing data and schema.

```bash
az monitor log-analytics workspace table migrate \
  --resource-group rg-sentinel \
  --workspace-name law-sentinel \
  --name CdsDeployments_CL
```

In Terraform:

```hcl
resource "terraform_data" "migrate_table" {
  provisioner "local-exec" {
    command = <<-EOT
      az monitor log-analytics workspace table migrate \
        --resource-group ${var.resource_group_name} \
        --workspace-name ${var.log_analytics_workspace_name} \
        --name ${var.table_name}_CL
    EOT
  }

  triggers_replace = [var.table_name]
}
```

> **Note**: Migration is idempotent — running it on an already-migrated table is a no-op. The table name, data, and schema are all preserved.

## Data Collection Rule (DCR) — With Suffix Transformation

The key insight: the **stream declaration** defines what the forwarder SENDS (raw JSON keys, no suffixes). The **transform_kql** maps those raw keys to the existing table columns (with suffixes). This means **your code doesn't change** — only the infrastructure.

### Example: Simple flat JSON (no nesting)

If your action currently sends:
```json
{"product": "my-app", "sha": "abc123", "repository": "cds-snc/app", "environment": "production"}
```

And your existing table has columns: `product_s`, `sha_s`, `repository_s`, `environment_s`

```hcl
resource "azurerm_monitor_data_collection_rule" "this" {
  name                        = "dcr-${lower(var.table_name)}"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.this.id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "log-analytics-destination"
    }
  }

  data_flow {
    streams       = ["Custom-${var.table_name}_CL"]
    destinations  = ["log-analytics-destination"]
    output_stream = "Custom-${var.table_name}_CL"
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | project-rename product_s = product, sha_s = sha, repository_s = repository, environment_s = environment
    KQL
  }

  # Stream declaration matches the RAW JSON your code sends (no suffixes)
  stream_declaration {
    stream_name = "Custom-${var.table_name}_CL"

    column { name = "TimeGenerated" type = "datetime" }
    column { name = "product"       type = "string" }
    column { name = "sha"           type = "string" }
    column { name = "repository"    type = "string" }
    column { name = "environment"   type = "string" }
  }

  depends_on = [terraform_data.migrate_table]
}
```

### Example: JSON with nested objects (flattening)

If your action currently sends:
```json
{
  "product": "my-app",
  "sha": "abc123",
  "details": {
    "env": "production",
    "region": "ca-central-1",
    "count": 3
  },
  "enabled": true
}
```

And your existing table has columns: `product_s`, `sha_s`, `details_env_s`, `details_region_s`, `details_count_d`, `enabled_b`

```hcl
resource "azurerm_monitor_data_collection_rule" "nested_example" {
  name                        = "dcr-${lower(var.table_name)}"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.this.id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "log-analytics-destination"
    }
  }

  data_flow {
    streams       = ["Custom-${var.table_name}_CL"]
    destinations  = ["log-analytics-destination"]
    output_stream = "Custom-${var.table_name}_CL"
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | extend product_s = tostring(product)
      | extend sha_s = tostring(sha)
      | extend details_env_s = tostring(details.env)
      | extend details_region_s = tostring(details.region)
      | extend details_count_d = todouble(details.count)
      | extend enabled_b = tobool(enabled)
      | project TimeGenerated, product_s, sha_s, details_env_s, details_region_s, details_count_d, enabled_b
    KQL
  }

  # Stream declaration matches the RAW JSON (accepts nested objects as dynamic)
  stream_declaration {
    stream_name = "Custom-${var.table_name}_CL"

    column { name = "TimeGenerated" type = "datetime" }
    column { name = "product"       type = "string" }
    column { name = "sha"           type = "string" }
    column { name = "details"       type = "dynamic" }
    column { name = "enabled"       type = "boolean" }
  }

  depends_on = [terraform_data.migrate_table]
}
```

### Example: Using a generic passthrough for any JSON

If you have many fields or the schema changes frequently, accept everything as a single `dynamic` column and use KQL to extract:

```hcl
resource "azurerm_monitor_data_collection_rule" "generic" {
  name                        = "dcr-${lower(var.table_name)}"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.this.id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "log-analytics-destination"
    }
  }

  data_flow {
    streams       = ["Custom-${var.table_name}_CL"]
    destinations  = ["log-analytics-destination"]
    output_stream = "Custom-${var.table_name}_CL"
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | extend RawData = pack_all()
      | project TimeGenerated, RawData
    KQL
  }

  stream_declaration {
    stream_name = "Custom-${var.table_name}_CL"

    column { name = "TimeGenerated" type = "datetime" }
    column { name = "RawData"       type = "dynamic" }
  }

  depends_on = [terraform_data.migrate_table]
}
```

> **Trade-off**: The generic approach requires KQL `extend` at query time to extract fields. The explicit approach gives you typed columns you can filter/aggregate directly.

## Helper: Generating the DCR from an Existing Table

Use this script to auto-generate the `stream_declaration` and `transform_kql` from your existing table schema:

```bash
#!/bin/bash
# Usage: ./generate-dcr-config.sh <resource-group> <workspace-name> <table-name>
RG="$1"
WS="$2"
TABLE="$3"

echo "Fetching schema for ${TABLE}_CL..."
COLUMNS=$(az monitor log-analytics workspace table show \
  --resource-group "$RG" \
  --workspace-name "$WS" \
  --name "${TABLE}_CL" \
  --query "schema.columns[?!starts_with(name, '_') && name != 'TenantId' && name != 'Type' && name != 'MG' && name != 'ManagementGroupName' && name != 'SourceSystem' && name != 'Computer'].{name: name, type: type}" \
  --output json)

echo ""
echo "=== Stream Declaration (raw JSON keys) ==="
echo "These go in stream_declaration. Map suffixed names back to raw names:"
echo ""
echo "$COLUMNS" | python3 -c "
import json, sys
columns = json.load(sys.stdin)

type_map = {'string': 'string', 'real': 'real', 'int': 'int', 'bool': 'boolean', 'datetime': 'datetime', 'dynamic': 'dynamic', 'long': 'long'}
suffix_map = {'_s': 'string', '_d': 'real', '_b': 'boolean', '_t': 'datetime', '_g': 'string'}

print('stream_declaration {')
print('  stream_name = \"Custom-${TABLE}_CL\"')
print('')
# TimeGenerated is always present
print('  column { name = \"TimeGenerated\" type = \"datetime\" }')

raw_to_suffixed = {}
for col in columns:
    name = col['name']
    col_type = col['type']
    if name == 'TimeGenerated':
        continue

    # Determine the raw field name (strip suffix)
    raw_name = name
    for suffix in ['_s', '_d', '_b', '_t', '_g', '_cf']:
        if name.endswith(suffix):
            raw_name = name[:-len(suffix)]
            break

    # Handle flattened nested objects (parent_child_s -> parent.child)
    # We group by top-level parent
    if '_' in raw_name:
        parts = raw_name.split('_')
        parent = parts[0]
        if parent not in raw_to_suffixed:
            raw_to_suffixed[parent] = []
        raw_to_suffixed[parent].append((name, col_type, raw_name))
    else:
        if raw_name not in raw_to_suffixed:
            raw_to_suffixed[raw_name] = []
        raw_to_suffixed[raw_name].append((name, col_type, raw_name))

# Determine stream columns (top-level raw fields)
seen_parents = set()
for raw_name, entries in raw_to_suffixed.items():
    if len(entries) > 1:
        # Multiple suffixed columns share a parent -> it was a nested object
        parent = raw_name
        if parent not in seen_parents:
            print(f'  column {{ name = \"{parent}\" type = \"dynamic\" }}')
            seen_parents.add(parent)
    else:
        suffixed_name, col_type, rn = entries[0]
        la_type = type_map.get(col_type, 'string')
        print(f'  column {{ name = \"{rn}\" type = \"{la_type}\" }}')

print('}')
print('')
print('=== Transform KQL ===')
print('transform_kql = <<-KQL')
print('  source')
print('  | extend TimeGenerated = now()')

for raw_name, entries in raw_to_suffixed.items():
    for suffixed_name, col_type, rn in entries:
        if suffixed_name == rn:
            # No suffix change needed, just rename
            print(f'  | project-rename {suffixed_name} = {rn}')
        elif '_' in rn and len(entries) > 1:
            # Flattened nested field
            parts = rn.split('_')
            parent = parts[0]
            child = '_'.join(parts[1:])
            cast = 'tostring'
            if col_type == 'real': cast = 'todouble'
            elif col_type == 'bool': cast = 'tobool'
            elif col_type == 'datetime': cast = 'todatetime'
            elif col_type == 'int' or col_type == 'long': cast = 'tolong'
            print(f'  | extend {suffixed_name} = {cast}({parent}.{child})')
        else:
            # Simple field with suffix added
            print(f'  | project-rename {suffixed_name} = {rn}')

print('  | project TimeGenerated, ' + ', '.join(col['name'] for col in columns if col['name'] != 'TimeGenerated'))
print('KQL')
" TABLE="$TABLE"

echo ""
echo "=== Done ==="
echo "Copy the above into your Terraform DCR resource."
```

> **Usage**: `./generate-dcr-config.sh rg-sentinel law-sentinel CdsDeployments`

## Entra App Registration with OIDC Federation

```hcl
# App registration
resource "azuread_application" "sentinel_forwarder" {
  display_name = "sentinel-forward-data-action"
}

resource "azuread_service_principal" "sentinel_forwarder" {
  client_id = azuread_application.sentinel_forwarder.client_id
}

# Federated credential for GitHub Actions OIDC
resource "azuread_application_federated_identity_credential" "github_oidc" {
  application_id = azuread_application.sentinel_forwarder.id
  display_name   = "github-actions-${var.github_repo}"
  description    = "GitHub Actions OIDC for ${var.github_org}/${var.github_repo}"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"
}
```

> **Subject claim options:**
> - Specific branch: `repo:org/repo:ref:refs/heads/main`
> - Any branch: `repo:org/repo:*` (less restrictive)
> - Specific environment: `repo:org/repo:environment:production`
> - Pull requests: `repo:org/repo:pull_request`

### Client Secret (for local testing only)

For local development/testing, you can create a client secret. This is **not needed** in GitHub Actions (OIDC is used instead).

```hcl
resource "azuread_application_password" "local_testing" {
  application_id = azuread_application.sentinel_forwarder.id
  display_name   = "local-testing"
  end_date       = timeadd(timestamp(), "720h") # 30 days
}

output "client_secret" {
  description = "Client secret for local testing (set as AZURE_CLIENT_SECRET)"
  value       = azuread_application_password.local_testing.value
  sensitive   = true
}
```

To use locally:
```bash
export AZURE_TENANT_ID="<your-tenant-id>"
export AZURE_CLIENT_ID="<output of azuread_application.sentinel_forwarder.client_id>"
export AZURE_CLIENT_SECRET="<output of client_secret>"
```

## Role Assignments

The service principal needs `Monitoring Metrics Publisher` on **both** the DCR and the DCE.

```hcl
# Required: permission to send data via the DCR
resource "azurerm_role_assignment" "dcr_metrics_publisher" {
  scope                = azurerm_monitor_data_collection_rule.this.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azuread_service_principal.sentinel_forwarder.object_id
}

# Required: permission to access the DCE ingestion endpoint
resource "azurerm_role_assignment" "dce_metrics_publisher" {
  scope                = azurerm_monitor_data_collection_endpoint.this.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azuread_service_principal.sentinel_forwarder.object_id
}
```

> **Note**: Both role assignments are required. Without the DCE role, you'll get a 403 error when the client tries to connect to the ingestion endpoint. Allow up to 5 minutes for role assignments to propagate.

## Outputs

These are the values you need for the GitHub Action inputs.

```hcl
output "dce_endpoint" {
  description = "Data Collection Endpoint logs ingestion URI"
  value       = azurerm_monitor_data_collection_endpoint.this.logs_ingestion_endpoint
}

output "dcr_rule_id" {
  description = "Immutable ID of the Data Collection Rule"
  value       = azurerm_monitor_data_collection_rule.this.immutable_id
}

output "stream_name" {
  description = "Stream name for the action input"
  value       = "Custom-${var.table_name}_CL"
}

output "client_id" {
  description = "Entra app client ID for azure/login"
  value       = azuread_application.sentinel_forwarder.client_id
}
```

## Complete Example: Migrating an Existing Deployment Tracker

This example shows migrating an existing `CdsDeployments_CL` table that was created by v1. The action currently sends:

```json
{"product": "my-app", "sha": "abc123", "repository": "cds-snc/app", "environment": "production"}
```

The old API created table columns: `product_s`, `sha_s`, `repository_s`, `environment_s`. **The JSON payload stays the same** — the DCR handles the mapping.

### terraform.tfvars

```hcl
resource_group_name          = "rg-sentinel"
location                     = "canadacentral"
log_analytics_workspace_id   = "/subscriptions/xxx/resourceGroups/rg-sentinel/providers/Microsoft.OperationalInsights/workspaces/law-sentinel"
log_analytics_workspace_name = "law-sentinel"
github_org                   = "cds-snc"
github_repo                  = "my-app"
table_name                   = "CdsDeployments"
```

### main.tf

```hcl
# 1. Migrate existing table (one-time, idempotent)
resource "terraform_data" "migrate_table" {
  provisioner "local-exec" {
    command = <<-EOT
      az monitor log-analytics workspace table migrate \
        --resource-group ${var.resource_group_name} \
        --workspace-name ${var.log_analytics_workspace_name} \
        --name ${var.table_name}_CL
    EOT
  }
  triggers_replace = [var.table_name]
}

# 2. Shared DCE
resource "azurerm_monitor_data_collection_endpoint" "this" {
  name                          = "dce-sentinel-forwarder"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  public_network_access_enabled = true
}

# 3. DCR with suffix transformation
resource "azurerm_monitor_data_collection_rule" "this" {
  name                        = "dcr-cdsdeployments"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.this.id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "log-analytics-destination"
    }
  }

  data_flow {
    streams       = ["Custom-CdsDeployments_CL"]
    destinations  = ["log-analytics-destination"]
    output_stream = "Custom-CdsDeployments_CL"
    # Rename raw fields to match existing suffixed columns
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | project-rename product_s = product, sha_s = sha, repository_s = repository, environment_s = environment
      | project TimeGenerated, product_s, sha_s, repository_s, environment_s
    KQL
  }

  # Stream declaration: what the forwarder SENDS (raw JSON keys, no suffixes)
  stream_declaration {
    stream_name = "Custom-CdsDeployments_CL"

    column { name = "TimeGenerated" type = "datetime" }
    column { name = "product"       type = "string" }
    column { name = "sha"           type = "string" }
    column { name = "repository"    type = "string" }
    column { name = "environment"   type = "string" }
  }

  depends_on = [terraform_data.migrate_table]
}

# 4. Entra app + OIDC
resource "azuread_application" "sentinel_forwarder" {
  display_name = "sentinel-forward-data-action"
}

resource "azuread_service_principal" "sentinel_forwarder" {
  client_id = azuread_application.sentinel_forwarder.client_id
}

resource "azuread_application_federated_identity_credential" "github_oidc" {
  application_id = azuread_application.sentinel_forwarder.id
  display_name   = "github-actions-${var.github_repo}"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"
}

# 5. Permissions (both DCR and DCE)
resource "azurerm_role_assignment" "dcr_metrics_publisher" {
  scope                = azurerm_monitor_data_collection_rule.this.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azuread_service_principal.sentinel_forwarder.object_id
}

resource "azurerm_role_assignment" "dce_metrics_publisher" {
  scope                = azurerm_monitor_data_collection_endpoint.this.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azuread_service_principal.sentinel_forwarder.object_id
}
```

### GitHub Actions workflow (only changes from v1 → v2)

**Before (v1):**
```yaml
- uses: cds-snc/sentinel-forward-data-action@main
  with:
    input_data: '{"product": "my-app", "sha": "${{ github.sha }}", "repository": "${{ github.repository }}", "environment": "production"}'
    log_type: CdsDeployments
    log_analytics_workspace_id: ${{ secrets.LOG_ANALYTICS_WORKSPACE_ID }}
    log_analytics_workspace_key: ${{ secrets.LOG_ANALYTICS_WORKSPACE_KEY }}
```

**After (v2):**
```yaml
permissions:
  id-token: write  # Add this at job level

steps:
  # Add azure/login step before the action
  - uses: azure/login@v2
    with:
      client-id: ${{ vars.AZURE_CLIENT_ID }}
      tenant-id: ${{ vars.AZURE_TENANT_ID }}
      subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

  - uses: cds-snc/sentinel-forward-data-action@main
    with:
      input_data: '{"product": "my-app", "sha": "${{ github.sha }}", "repository": "${{ github.repository }}", "environment": "production"}'
      dce_endpoint: ${{ vars.SENTINEL_DCE_ENDPOINT }}
      dcr_rule_id: ${{ vars.SENTINEL_DCR_RULE_ID }}
      stream_name: ${{ vars.SENTINEL_STREAM_NAME }}
```

> **Notice**: The `input_data` JSON is exactly the same. No `_s` suffixes needed in your code — the DCR transformation handles it.

## Complete Example: Nested Objects (Flattening)

If your action sends nested JSON:

```json
{
  "service": "api-gateway",
  "alert": {
    "severity": "high",
    "message": "CPU threshold exceeded",
    "count": 5
  },
  "resolved": false
}
```

Existing table columns: `service_s`, `alert_severity_s`, `alert_message_s`, `alert_count_d`, `resolved_b`

```hcl
resource "azurerm_monitor_data_collection_rule" "alerts" {
  name                        = "dcr-cdsalerts"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  data_collection_endpoint_id = azurerm_monitor_data_collection_endpoint.this.id

  destinations {
    log_analytics {
      workspace_resource_id = var.log_analytics_workspace_id
      name                  = "log-analytics-destination"
    }
  }

  data_flow {
    streams       = ["Custom-CdsAlerts_CL"]
    destinations  = ["log-analytics-destination"]
    output_stream = "Custom-CdsAlerts_CL"
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | extend service_s = tostring(service)
      | extend alert_severity_s = tostring(alert.severity)
      | extend alert_message_s = tostring(alert.message)
      | extend alert_count_d = todouble(alert.count)
      | extend resolved_b = tobool(resolved)
      | project TimeGenerated, service_s, alert_severity_s, alert_message_s, alert_count_d, resolved_b
    KQL
  }

  # Stream matches raw JSON structure (nested objects as dynamic)
  stream_declaration {
    stream_name = "Custom-CdsAlerts_CL"

    column { name = "TimeGenerated" type = "datetime" }
    column { name = "service"       type = "string" }
    column { name = "alert"         type = "dynamic" }
    column { name = "resolved"      type = "boolean" }
  }

  depends_on = [terraform_data.migrate_table]
}
```

## Multiple Tables with a Shared DCE

For multiple tables, use a module pattern. Each table gets its own DCR with its own transformation:

```hcl
# Shared DCE (one per region)
resource "azurerm_monitor_data_collection_endpoint" "shared" {
  name                          = "dce-sentinel-forwarder"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  public_network_access_enabled = true
}

# Per-table module
module "sentinel_table" {
  source   = "./modules/sentinel-table"
  for_each = var.tables

  resource_group_name          = var.resource_group_name
  location                     = var.location
  log_analytics_workspace_id   = var.log_analytics_workspace_id
  log_analytics_workspace_name = var.log_analytics_workspace_name
  data_collection_endpoint_id  = azurerm_monitor_data_collection_endpoint.shared.id
  table_name                   = each.key
  stream_columns               = each.value.stream_columns
  transform_kql                = each.value.transform_kql
  principal_id                 = azuread_service_principal.sentinel_forwarder.object_id
}
```

Where `var.tables`:

```hcl
tables = {
  CdsDeployments = {
    stream_columns = [
      { name = "TimeGenerated", type = "datetime" },
      { name = "product",       type = "string" },
      { name = "sha",           type = "string" },
      { name = "repository",    type = "string" },
      { name = "environment",   type = "string" },
    ]
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | project-rename product_s = product, sha_s = sha, repository_s = repository, environment_s = environment
      | project TimeGenerated, product_s, sha_s, repository_s, environment_s
    KQL
  }
  CdsAlerts = {
    stream_columns = [
      { name = "TimeGenerated", type = "datetime" },
      { name = "service",       type = "string" },
      { name = "alert",         type = "dynamic" },
      { name = "resolved",      type = "boolean" },
    ]
    transform_kql = <<-KQL
      source
      | extend TimeGenerated = now()
      | extend service_s = tostring(service)
      | extend alert_severity_s = tostring(alert.severity)
      | extend alert_message_s = tostring(alert.message)
      | extend alert_count_d = todouble(alert.count)
      | extend resolved_b = tobool(resolved)
      | project TimeGenerated, service_s, alert_severity_s, alert_message_s, alert_count_d, resolved_b
    KQL
  }
}
```

## Migration Checklist

For each repository currently using v1:

1. **Discover schema**: Run `az monitor log-analytics workspace table show` to get existing columns
2. **Migrate table**: `az monitor log-analytics workspace table migrate --name YourTable_CL`
3. **Create DCR**: Define stream declaration (raw keys) + transform_kql (rename to suffixed columns)
4. **Assign permissions**: `Monitoring Metrics Publisher` role on both the DCR and the DCE for the Entra app
5. **Update workflow**: Replace `log_analytics_workspace_id`/`key`/`log_type` with `dce_endpoint`/`dcr_rule_id`/`stream_name` + add `azure/login`
6. **Keep JSON unchanged**: The `input_data` / file contents stay exactly the same
7. **Verify**: Check Log Analytics for new rows after first run

> **The only changes in your workflow YAML are**: add `azure/login`, replace 3 credential inputs with 3 new inputs. Your JSON data and application code remain untouched.
