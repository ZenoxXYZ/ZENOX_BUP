# Requirements Normalization Prompt

## Use

After challenge intake is reviewed.

```text
Read AGENTS.md, the Builder workflow, official rules/clarifications, authoritative challenge source or approved intake analysis, and repository state. Propose a normalized problem definition without editing files.

Cover only evidence-supported objective, actors, capabilities, concepts/entities, inputs, outputs, constraints, stated validation/business requirements, external systems, evaluation criteria, deployment requirement if explicitly stated, ambiguities, unspecified decisions, and supported deferrals. Mark important conclusions [PROBLEM REQUIREMENT], [UNSPECIFIED], or [OUR DESIGN DECISION]. Do not design architecture, APIs, persistence, algorithms, deployment, or frontend behavior. Stop for human approval.

After explicit approval, update problem.md exactly to that approved interpretation. Preserve labels and do not begin product design, modify unrelated files, commit, or push.
```
