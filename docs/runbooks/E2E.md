# End-To-End Verification

> **Product Build specialization.** Browser E2E is a Product Build verification
> mechanism, not universal HADF verification. See the [Product Build playbook](../playbooks/product-build.md).

Run E2E after the required capabilities assemble into the Golden Path. Use the real selected runtime path and prove the intended user outcome across required layers.

```text
user action -> frontend if present -> API -> backend -> persistence/logic
-> response -> visible result -> refresh/reload where relevant
```

For local release, verify browser/app -> local frontend where present -> local backend -> local/test database, then confirm refresh/reload and persisted result where relevant. Local E2E does not prove deployed E2E.

If deployment is selected, verify browser -> hosted frontend -> production API URL -> hosted backend -> hosted database. Confirm public health, frontend API configuration, no hard-coded localhost dependency, HTTPS/origin behavior, CORS, hosted persistence, applied migrations, production error behavior, and the deployed Golden Path.
