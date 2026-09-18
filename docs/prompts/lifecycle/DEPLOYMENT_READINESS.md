# Deployment Readiness Prompt

> **Product Build specialization.** Deployment remains conditional; see the [Product Build playbook](../../playbooks/product-build.md).

## Use

After Golden-Path assembly, systematic hardening, local E2E, and Feature Freeze.

```text
Read AGENTS.md, the Builder workflow, full-stack/deployment runbooks, official rules when supplied, approved state files, code, configuration, migrations, dependencies, tests, deployment evidence, and Git state. Reconstruct the locally verified release state.

First decide whether deployment is permitted and justified by rules, demo needs, reliability, and time. If local E2E is the safer path, recommend it and stop. If deployment is approved, propose the smallest architecture for [TARGET]: backend/frontend hosting, hosted database, environment variable names, production startup, migrations, production API URL, CORS, external-service access/fallback, secrets, verification, fallback demo, files, risks, and deferrals. Do not add infrastructure by default or mutate real hosted data. Stop for approval.

After explicit approval, configure only approved deployment changes. Verify public health, frontend if present, production API usage, CORS, hosted persistence/migration status, and deployed Golden Path. Report URLs, environment-variable names only, evidence, risks, fallback, and unverified items. Do not commit or push.
```
