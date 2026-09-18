# Challenge Classification

## Purpose

Classify the challenge before selecting technology or a specialized workflow. A
Challenge Profile records its shape; it does not prescribe a solution.

## Challenge Profile

| Axis | Record one or more applicable values |
| --- | --- |
| Starting State | S0 Greenfield; S1 Constrained scaffold; S2 Existing product/repository/system; S3 Physical/cyber-physical environment |
| Engineering Objective | BUILD; COMPLETE; INTEGRATE; REPAIR; SECURE; OPTIMIZE; OPERATE; DESIGN; ANALYZE |
| Evaluation Contract | HUMAN DEMO; AUTOMATED CHECKER; HIDDEN TESTS; BENCHMARK; SECURITY VALIDATION; UPSTREAM REVIEW; PHYSICAL MEASUREMENT; SIMULATION RESULT; COMPLIANCE / STANDARD; DESIGN REVIEW; HYBRID |
| Dominant Artifact | PRODUCT; API / SERVICE; AI PIPELINE; ALGORITHM; PATCH; INFRASTRUCTURE; HARDWARE SYSTEM; SECURITY FINDING / FIX; DATASET; MODEL; CAD / BIM ARTIFACT; SIMULATION; ENGINEERING DESIGN; UPSTREAM PR; HYBRID |
| Realization / Proof Mode | R0 Executable software; R1 Physical prototype; R2 Embedded / cyber-physical prototype; R3 Simulation; R4 CAD / BIM / engineering model; R5 Dataset / model / analytical artifact; R6 Benchmark result; R7 Patch / integration; R8 Security evidence; R9 Experimental proof-of-concept; R10 Hybrid |

## How To Classify

Use official sources and supplied assets. Record only values supported by those
sources, mark uncertainty explicitly, and use `HYBRID` only when no single
value represents the challenge well enough.

Technology is not a classification axis. Two AI or web challenges may require
different workflows because their evaluation contract or proof mode differs.

## Recording The Profile

Record the approved profile in `problem.md`; repeat it in `plan.md` only to
show the selected strategy. Keep `Primary Playbook Candidate` as `TBD` or
provisional until a playbook layer exists.

## Brief Examples

- An existing service with hidden tests can be S2, REPAIR, HIDDEN TESTS, PATCH,
  and R7.
- A representative railway simulation can be S3, OPTIMIZE, SIMULATION RESULT,
  SIMULATION, and R3.

Examples classify challenge shape only; they do not create requirements.
