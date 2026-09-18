# Pull Request Workflow

A PR is a reviewable proposal for one bounded branch. It records the workstream, Golden-Path relevance, approved contract, implementation scope, tests, risks, dependencies, review state, and post-merge work using the repository template.

PR lifecycle:

```text
Local Complete -> human diff review -> commit -> push -> PR -> CI
-> review -> fixes or accepted findings -> merge
```

CI is automated configured checking. PR review is human or reviewer judgment about scope, architecture, contracts, and code. Neither proves integrated runtime behavior.
