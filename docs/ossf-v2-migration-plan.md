# OSSF Scorecard → v2 Forwarder Migration Plan

## Goal

Convert the `ossf-scorecard.yml` workflow in this repo (and later all 57+ OSSF repos) from the v1 Data Collector API to the v2 Logs Ingestion API.

---

## Prerequisites (Azure / Terraform — all in `cds-snc/sentinel` repo)

All infrastructure changes live in the **`cds-snc/sentinel`** repo. See
[docs/sentinel-forwarder-v2-infra-plan.md](sentinel-forwarder-v2-infra-plan.md) for the
detailed execution plan to hand off to that repo.

### Summary of what the sentinel repo needs to create

1. **App Registration** for the forwarder v2 with a client secret (stored as org-level GitHub secret)
2. **Data Collection Endpoint (DCE)** — one shared endpoint for all forwarder v2 ingestion
3. **Data Collection Rules (DCRs)** — one per log type / custom table (OSSF first, then the rest)
4. **Role assignments** — Monitoring Metrics Publisher on each DCR for the app registration
5. **Org-level GitHub secrets** — Azure creds (client ID, client secret, tenant ID), DCE endpoint, per-table DCR rule IDs + stream names

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
- name: "Post results to Sentinel"
  uses: cds-snc/sentinel-forward-data-action@main
  env:
    AZURE_TENANT_ID: ${{ secrets.SENTINEL_V2_AZURE_TENANT_ID }}
    AZURE_CLIENT_ID: ${{ secrets.SENTINEL_V2_AZURE_CLIENT_ID }}
    AZURE_CLIENT_SECRET: ${{ secrets.SENTINEL_V2_AZURE_CLIENT_SECRET }}
  with:
    file_name: ossf-results-modified.json
    dce_endpoint: ${{ secrets.SENTINEL_DCE_ENDPOINT }}
    dcr_rule_id: ${{ secrets.SENTINEL_DCR_RULE_ID_OSSF }}
    stream_name: ${{ secrets.SENTINEL_STREAM_NAME_OSSF }}
```

> No `azure/login` step or `id-token: write` permission needed — `DefaultAzureCredential`
> picks up `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET` from env vars.

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
- [ ] Monitor for `DefaultAzureCredential` auth failures in Actions logs

## Cleanup (after full rollout)

- [ ] Remove org secrets `LOG_ANALYTICS_WORKSPACE_ID` and `LOG_ANALYTICS_WORKSPACE_KEY` once no repos reference them
- [ ] Set a calendar reminder to rotate `SENTINEL_V2_AZURE_CLIENT_SECRET` before expiry
- [ ] Consider deprecating the v1 code path in the action
