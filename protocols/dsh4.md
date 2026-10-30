# DSH-4: is the agentic scaffold worth more than sampling the same model N times?

Registered 2026-09-25, BEFORE any scored episode. Final question of the DSH
program. Runs on the cluster.

## Why this is the decision-relevant question

DSH-3 established the agent reaches PARITY with greedy single-shot at 14b/32b
while costing 8-9x the wall time, and that it covers a few tasks single-shot
misses (+2 to +6). The obvious objection to treating that coverage as
valuable: **the same compute buys ~8-9 sampled single-shot attempts**, and
a standard inference-time lever is best-of-N sampling with a verifier. So the real question is not "agent vs one shot" -- DSH-1
and DSH-3 answered that -- it is **"agent vs the cheapest thing you could do
with the same budget"**.

Measured matched budget from DSH-3, per task:
- 14b: single-shot 4.2 s / 160 tok; agent 33.0 s / 926 tok -> **N = 8**
- 32b: single-shot 9.3 s / 171 tok; agent 83.9 s / 1158 tok -> **N = 9**

Using the wall-matched N (the more generous to the agent of the two).

## Arms (rungs 14b and 32b; 8b is settled and not re-run)

- **A (reference)**: greedy single-shot, unchanged, temp 0.0. Deterministic,
  re-verified.
- **C (treatment)**: **N=8 sampled single-shot candidates**, temp 0.6 -- the
  agent's own sampling temperature -- each scored independently against the
  hidden tests. Reported as the pass@k curve for k=1..8.
- **B (comparator)**: the dsh agent. DSH-3's three sessions per rung are
  reused as the comparator distribution; B is NOT re-run, because C is being
  compared to an already-measured distribution and re-running B would only
  add cost, not validity. Stated plainly: C is new data, B is DSH-3 data from
  the same node, same serving stack, same manifest, days earlier.

## pass@N is an ORACLE CEILING, and will be labelled as one everywhere

pass@8 counts a task solved if ANY of the 8 samples passes the hidden tests.
No real system can do that without the hidden tests, so it is an UPPER BOUND
on every best-of-N selection rule, not an achievable score. My rule against best-of-N capability claims
() is respected: no capability
claim is made from pass@N, it is used only as a ceiling.

## Pre-committed readings (written before any DSH-4 episode runs)

- **agent > pass@8 ceiling**: the scaffold contributes something sampling
  cannot buy. This would be the program's first positive result for agentic
  scaffolding and would still need an independent replication before use.
- **pass@1 < agent < pass@8**: the scaffold beats a single shot but is
  dominated by an IDEALISED selector. Not decisive against the agent, because
  the ceiling is unreachable; the follow-up would be a realisable selector
  (select by the candidate's own self-written tests, which is what the agent
  itself does).
- **agent <= pass@1-ish**: the scaffold adds nothing beyond one shot and the
  complementarity seen in DSH-3 is sampling noise. The DSH programme closes
  with a clean negative.
- The pass@k curve's shape is reported regardless: if pass@k saturates by
  k=3, then "8 samples" is not really the alternative on offer and the honest
  comparison is against the saturation point.

## Method notes

Same 98-task frozen manifest, same verifier, same exclusive-node serving
stack (`OLLAMA_LLM_LIBRARY=cuda_v12`, 8192 ctx). Each of the 8 samples is an
independent request with a distinct seed; sampling parameters are sent
explicitly on every request
(). Candidates that yield no
fenced code block are failures, not exclusions. All data rsynced to the Mac
with a superset check; nothing kept on compute nodes.
