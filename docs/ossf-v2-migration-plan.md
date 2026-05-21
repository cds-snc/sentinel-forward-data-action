# OSSF Scorecard → v2 Forwarder Migration Plan

## Goal

Convert the `ossf-scorecard.yml` workflow in this repo (and later all 57+ OSSF repos) from the v1 Data Collector API to the v2 Logs Ingestion API.

---

## Prerequisites (Azure / Terraform)

Infrastructure changes are split across two repos:
- **`cds-snc/cds-azure-resources`** — App Registration + flexible federated identity credential + DCE
- **`cds-snc/sentinel`** — DCRs, custom tables, and role assignments

See [sentinel-forwarder-v2-infra-plan.md](sentinel-forwarder-v2-infra-plan.md) for the
detailed execution plan.

### Summary of what needs to be created

1. **App Registration** with a flexible federated identity credential (`claims['sub'] matches 'repo:cds-snc/*'`) — one credential covers all repos (in `cds-azure-resources`)
2. **Data Collection Endpoint (DCE)** — one shared endpoint (in `cds-azure-resources`)
3. **Data Collection Rules (DCRs)** — one per log type / custom table, OSSF first (in `sentinel`)
4. **Role assignments** — Monitoring Metrics Publisher on each DCR for the app registration (in `sentinel`)
5. **Org-level GitHub secrets** — Azure OIDC creds, DCE endpoint, per-table DCR rule IDs + stream names

---

## Workflow Changes (this repo first, then rollout)

### 5. Update `ossf-scorecard.yml`

**Current (v1):**
```yaml
- name: "Post results to Sentinel"
  uses: cds-snc/sentinel-forward-data-action@01db4a9203054ecdb60ff368c3cdfca71d62e85f
  with:
    file_name: ossf-results-modified.json
    log_type: GitHubMetadata_OSSF_Scorecard
    log_analytics_workspace_id: ${{ secrets.LOG_ANALYTICS_WORKSPACE_ID }}
    log_analytics_workspace_key: ${{ secrets.LOG_ANALYTICS_WORKSPACE_KEY }}
```

**Target (v2):**
```yaml
- name: "Login to Azure"
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.SENTINEL_V2_AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.SENTINEL_V2_AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.SENTINEL_V2_AZURE_SUBSCRIPTION_ID }}

- name: "Post results to Sentinel"
  uses: cds-snc/sentinel-forward-data-action@main
  with:
    file_name: ossf-results-modified.json
    dce_endpoint: ${{ secrets.SENTINEL_DCE_ENDPOINT }}
    dcr_rule_id: ${{ secrets.SENTINEL_DCR_RULE_ID_OSSF }}
    stream_name: ${{ secrets.SENTINEL_STREAM_NAME_OSSF }}
```

**Additional workflow change — add OIDC permission:**
```yaml
permissions:
  contents: read
  issues: read
  pull-requests: read
  checks: read
  actions: read
  id-token: write  # ← required for OIDC with azure/login
```

---

## Rollout Order

| Phase | Scope | Action |
|-------|-------|--------|
| 1 | This repo (`sentinel-forward-data-action`) | Update workflow, verify data lands in new table |
| 2 | 1-2 pilot repos (e.g. `cds-azure-resources`, `sre-bot`) | Confirm org secrets work cross-repo |
| 3 | Remaining 55 OSSF-only repos | Batch PRs (can be scripted/Renovate) |
| 4 | 17 custom-usage repos | Requires per-repo DCR/stream for each table |

---

## Validation

- [ ] After phase 1: query `GitHubMetadata_OSSF_Scorecard_CL` in Log Analytics to confirm v2 data arrives
- [ ] Compare v1 vs v2 records side-by-side to verify schema parity
- [ ] Monitor for OIDC / `azure/login` auth failures in Actions logs

## Cleanup (after full rollout)

- [ ] Remove org secrets `LOG_ANALYTICS_WORKSPACE_ID` and `LOG_ANALYTICS_WORKSPACE_KEY` once no repos reference them
- [ ] Consider deprecating the v1 code path in the action
