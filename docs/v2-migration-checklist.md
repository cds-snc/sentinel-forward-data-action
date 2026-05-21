# sentinel-forward-data-action v2 Migration Checklist

> **Generated:** 2025-05-11
> **Source:** GitHub code search across `cds-snc` org for `cds-snc/sentinel-forward-data-action` in `.github/workflows/`

## Repos with Custom Workflow Usage (non-OSSF)

These repos use the action for deployment reporting, vulnerability scanning, or other custom data forwarding — higher priority for migration.

- [ ] **ai-answers** — `build_and_deploy_production.yml`, `build_and_deploy_staging.yml`, `ossf-scorecard.yml`
- [ ] **automatic-website-scanning** — `oswasp-zap-default.yml`, `a11ywatch.yml`, `nuclei-default.yml`, `lighthouse.yml`, `ossf-scorecard.yml`
- [ ] **data-lake** — `terragrunt-apply-production.yml`, `terragrunt-apply-staging.yml`, `ossf-scorecard.yml`
- [ ] **digital-canada-ca-website** — `build-push.yml`
- [ ] **dns-proxy-action** — `ci_docker_action.yml`, `ossf-scorecard.yml`
- [ ] **dto-feedback-cj** — `build_push_staging.yml`, `build_push_production.yml.disabled`
- [ ] **dto-feedback-viewer** — `build_and_deploy_staging.yml`
- [ ] **forms-api** — `staging-deploy.yml`, `prod-deploy.yml`, `ossf-scorecard.yml`
- [ ] **gc-articles** — `terragrunt-apply-staging.yml`, `deploy-production-container.yml`, `terragrunt-apply-production.yml`, `deploy-staging-container.yml`, `ossf-scorecard.yml`
- [ ] **gcds-components** — `compile-and-publish.yml`, `ossf-scorecard.yml`
- [ ] **gcds-css-shortcuts** — `publish.yml`, `ossf-scorecard.yml`
- [ ] **gcds-fonts** — `upload-cdn.yml`, `ossf-scorecard.yml`
- [ ] **gcds-tokens** — `publish.yml`, `ossf-scorecard.yml`
- [ ] **notification-manifests** — `helmfile_staging_apply.yaml`, `helmfile_production_apply.yaml`, `ossf-scorecard.yml`
- [ ] **platform-forms-client** — `prod-post-deployment.yml`, `staging-post-deployment.yml`, `ossf-scorecard.yml`
- [ ] **site-reliability-engineering** — `vulnerability_report.yml`, `ossf-scorecard.yml`
- [ ] **sre-bot** — `build_and_deploy.yml`, `ossf-scorecard.yml`

## Repos with OSSF Scorecard Usage Only

These repos only use the action in their `ossf-scorecard.yml` workflow.

- [ ] **aws-sentinel-connector-layer**
- [ ] **backstage-catalog-info-helper-action**
- [ ] **backstage-scaffolder-templates**
- [ ] **canadalogin-user-profile-sync-poc**
- [ ] **cds-aws-lz**
- [ ] **cds-azure-resources**
- [ ] **cds-superset**
- [ ] **cds-website-cms**
- [ ] **cds-website-pr-bot**
- [ ] **cds-website-terraform**
- [ ] **cloud-based-sensor**
- [ ] **credentials-gc-issue-verify-docs**
- [ ] **credentials-gc-issue-verify-mgmt**
- [ ] **credentials-issue-and-verify-service**
- [ ] **credentials-issue-verify-entraid-setup**
- [ ] **credentials-verifier-app**
- [ ] **credentials-wallet-app**
- [ ] **data-r-functions-for-cds**
- [ ] **dns**
- [ ] **forms-terraform**
- [ ] **gc-issue-and-verify-website**
- [ ] **gc-organisations**
- [ ] **gc-signin-sentinel**
- [ ] **gc-signin-static-website**
- [ ] **gc-signin-terraform**
- [ ] **gc-simple-dictionary**
- [ ] **gcds-docs**
- [ ] **gcds-examples**
- [ ] **gcds-figma-library**
- [ ] **gcds-figma-tokens**
- [ ] **gcorg-resolver**
- [ ] **ipv4-geolocate-webservice**
- [ ] **labels**
- [ ] **notification-admin**
- [ ] **notification-adr**
- [ ] **notification-api**
- [ ] **notification-document-download-api**
- [ ] **notification-documentation**
- [ ] **notification-go-client**
- [ ] **notification-terraform**
- [ ] **notification-utils**
- [ ] **oscal-compliance**
- [ ] **platform-unified-accounts**
- [ ] **pr-workflow-failure**
- [ ] **project-template**
- [ ] **renovate-app**
- [ ] **renovate-config**
- [ ] **sanitize-pii**
- [ ] **secret**
- [ ] **security-tools**
- [ ] **sentinel**
- [ ] **simplify-privacy-statements-V2**
- [ ] **site-reliability-engineering-public**
- [ ] **status-statut**
- [ ] **terraform-modules**
- [ ] **terraform-plan**
- [ ] **valentine-terraform**

---

**Total repos: 74** (17 with custom usage + 57 OSSF-only)
