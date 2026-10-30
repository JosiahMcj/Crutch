# DSH-2: is the agentic deficit caused by incremental file editing?

Registered 2026-08-26 20:10 MST, BEFORE any scored episode. Follow-up to

## The claim under test

DSH-1 concluded that the dsh minimal agent loses to single-shot at 8B, and
attributed it to a mechanism: **the agent corrupts its own solution file
through iterative `str_replace` editing** (301 failed replace-matches across
98 episodes; 13 syntactically invalid candidates; 8 of 9 physics losses were
syntax-invalid files rather than wrong answers).

That attribution is CORRELATIONAL. DSH-2 tests it by intervention: remove
the incremental-edit capability and see whether the losses come back.

## Prediction (pre-registered, falsifiable)

If the mechanism claim is right, an agent that can only write whole files
should recover most of the 10 syntax-invalid losses in this suite, and B2
should beat B1 significantly. **If B2 ~= B1, the editing explanation is
WRONG** and DSH-1's mechanism paragraph must be corrected to say the deficit
is something else (looping, context handling, or plain capability).

## Suite (frozen)

The two banks where the mechanism was observed, n = 48:
- `bank_physics` (28) -- B1 solved 19, 8 of its
  9 losses syntax-invalid.
- `bank_alg` (20) -- B1 solved 4, 2 of its 16 losses
  syntax-invalid.

`mbpp_blind` is deliberately EXCLUDED: B1 did best there (34/50) and the
mechanism barely operates, so those pairs would be mostly concordant and
contribute no power. This is registered as a **mechanism test on the strata
where the mechanism was observed**, NOT as a replication of DSH-1's
headline, and no 98-task claim will be restated from it.

Same manifest discipline as DSH-1 (task_id + README sha + tests sha written
before episode 1), same shuffle seed 42, arms back-to-back per task.

## Arms (both agentic; single-shot is NOT re-run)

Arm A is dropped on purpose: the B2-vs-A comparison conflates the scaffold
change with the registered sampling asymmetry (A greedy, B at temp 0.6), and
A's rate on this exact manifest was measured two days ago under identical
conditions. It may be quoted descriptively, never as a fresh paired test.

- **B1 (control)** -- exactly DSH-1's arm B: `composition-b1.yml`
  (persistent bash + `str_replace_editor`), DSH-1's frozen prompt.
- **B2 (treatment)** -- `composition-b2.yml`: identical EXCEPT the
  `str-replace-editor` component is removed, so bash is the only file
  surface and every write is a whole-file heredoc. The prompt differs only
  in the file-writing instruction.

The treatment is enforced by TOOL SURFACE, not by instruction. DSH-1 showed
that a prompt rule the model can ignore is not a treatment: it was told to
use absolute paths and mistyped them anyway.

Named consequence of the design: B2 has one tool where B1 has two. The
treatment is therefore "whole-file writes via bash, no editor tool" versus
"editor tool with incremental replace available" -- not "same tools minus
one command". Stated here so it is not discovered later.

## Treatment verification (config-class exclusions)

- Any `str_replace_editor` call in a B2 episode => the treatment did not
  happen => episode is a config-class InfraError, never scored. Expected
  zero by construction; asserted anyway (arm the trap so silence means
  something).
- Bash-mediated incremental edits in B2 (`sed -i`, `>>` appends, `patch`)
  are counted per episode and REPORTED. They are not exclusions -- they are
  the model routing around the intervention, which is itself a finding.

## Endpoints

- PRIMARY: paired B1 vs B2 solved/failed, McNemar exact two-sided on
  discordant pairs, alpha 0.05. Power lives in the discordant count, not in
  48; that count will be reported alongside every p-value.
- Secondary (registered): syntax-invalid rate per arm; wall-cap rate per arm
  (whole-file writing should need fewer turns, so a drop here is expected
  and is NOT evidence for the mechanism on its own); steps, wall seconds,
  output tokens, tool errors per arm; per-bank split.

## Inherited infrastructure (reused unchanged, not re-derived)

Wire shim on :11502 forcing `reasoning_effort: none`; think-burn detector;
transcript attribution guard; missing/ambiguous transcript => unscoreable;
env-vs-config unknown split; absolute run-dir; gpulock; KILL lever; torn
trailing record tolerance; hardened pilot gate. Every one was paid for by a
DSH-1 defect and none is being re-litigated.

Model, serving, verifier, wall cap (600 s), and max_tokens (4096) are
identical to DSH-1 so B1 is comparable to its DSH-1 self as a sanity check
(descriptive only -- the inferential comparison is B1 vs B2 within DSH-2,
because conditions do not replicate across sessions).

## Stops

- Pre-campaign known-positive: one live B2 episode on a physics task B1
  failed with a syntax-invalid file; transcript must show zero editor calls
  and produce a compilable file. Campaign does not start otherwise.
- Verdict by the paired-test procedure over the per-task JSONL only.
- Any change after registration = a written amendment BEFORE the affected
  episodes. Outcome-based voiding is forbidden.

## Pre-campaign known-positive (run 2026-08-26 20:11-20:21, before registration closed)

One live B2 episode on `newton2__solve_m` -- a physics task B1 lost in DSH-1
with an `unexpected indent` syntax error:

- tools used: **bash x60, str_replace_editor x0** (treatment enforced by the
  composition, verified in the transcript, not assumed)
- tool errors: 0; bash in-place edits: 0
- file written, compiles, and **passes the hidden test (all_passed=True)**

So the treatment happens and, on this instance, it converts exactly the
failure DSH-1 blamed on incremental editing. That is one episode, not
evidence for the campaign's conclusion -- it is the arm-the-trap check that
the intervention is real before spending the compute.

Noted for the record: the probe still ran to the 600 s cap with 60 bash
calls after having written a correct file, so B2 is not expected to be
cheaper in wall time; the cap-rate secondary may not move.

## ADDENDUM 2026-08-27 (registered before running): arm-A replication check

DSH-2 surfaced something its own endpoint does not address. B1 is byte-identical
to DSH-1's arm B (same composition, same prompt sha 2d10099f, same model, cap,
shim, verifier) and ran on the same 48 tasks, yet:

    DSH-1 arm B : 23/48      DSH-2 arm B1 : 32/48
    flips fail->pass 10, pass->fail 1  (sign test p = 0.012)

The control arm moved significantly between sessions. That does not invalidate
DSH-1's paired within-session comparison -- pairing is exactly what controls
session effects -- but it does mean the EFFECT SIZE is unstable, and any
generalisation from one session is weaker than DSH-1's write-up implies.

Discriminating question: is the instability specific to the agentic loop
(high-variance, 20+ sampled turns at temp 0.6) or environmental (the box, the
server, the model state)? Arm A is greedy at temperature 0 and near
deterministic, so re-running it is the test.

**Registered before running**: re-run arm A unchanged (`build_solution_prompt`,
think:false, temp 0.0, num_predict 2048) over the same frozen 48-task manifest,
~15 min. Pre-stated readings:
- A reproduces at or near 37/48 (say within +-2) => the instability is
  AGENTIC-ARM-SPECIFIC. DSH-1's direction stands but its effect size must be
  reported as session-dependent, and the honest fix is multi-session runs.
- A also moves by several tasks => the instability is ENVIRONMENTAL and DSH-1's
  headline is materially weaker than stated; the write-up must say so.

Either way the result is recorded. This is a replication check of an existing
arm, not a new comparison, and it changes no DSH-2 endpoint.
