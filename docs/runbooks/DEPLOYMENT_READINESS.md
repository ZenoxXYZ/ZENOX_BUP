# Deployment Readiness

> **Product Build specialization.** Deployment remains conditional on official
> rules, demo needs, and time; see the [Product Build playbook](../playbooks/product-build.md).

Deployment is conditional: select it only when official rules require it, the demo needs it, or it is a reliable use of remaining time. A local E2E release path is valid when those conditions do not apply.

After Golden-Path assembly, systematic hardening, local E2E, and Feature Freeze, choose one path:

```text
local final runtime -> chosen-runtime E2E -> P0/P1 corrections
```

or:

```text
deployment -> deployed E2E -> P0/P1 corrections
```

For deployment, verify hosting, environment variables by name only, production startup, frontend production API URL, CORS, approved hosted database/migrations, external-service access and fallback, public health, persistence, and the deployed Golden Path. Do not add containers, queues, or cloud complexity unless approved requirements or the chosen provider require them.
