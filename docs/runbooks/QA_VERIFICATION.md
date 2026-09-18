# QA Verification

QA verifies behavior and risk beyond configured CI. Select checks from the
evaluation contract and artifact: successful behavior, important failure and
boundary cases, interface/assumption adherence, integration risks, evidence
limits, recovery, and cross-component interactions where applicable.

Where a browser exists for Product Build work, inspect Network activity to
confirm request URL, method, payload, response, status, CORS behavior, and the
absence of accidental mock or localhost dependencies. Classify evidence
accurately: CI checks automation, review judges changes, QA verifies behavior,
and E2E verifies an assembled Product Build journey. Record failures, retests,
regressions, and remaining risks in `review.md` or detailed review evidence as
appropriate.
