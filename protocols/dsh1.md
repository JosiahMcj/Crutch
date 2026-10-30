# DSH-1: agentic scaffold (DeepSeek Harness) vs single-shot, same model, same verifier

Registered 2026-08-22, BEFORE any scored run. Pilot episodes for wiring
(explicitly excluded) are permitted only on tasks OUTSIDE the frozen suite.

## Question

Holding the model, the tasks, and the verifier fixed, does wrapping the model
in an agentic scaffold -- DeepSeek Harness (dsh) minimal agent: multi-turn,
persistent bash + str_replace_editor, allowed to write and run its OWN tests --
change the verified solve rate relative to a single-shot generator?

This question matters because sampling several answers and checking them with a verifier is a standard inference-time lever, and an agentic scaffold is the other family. Nothing here trains weights.

## Fixed factors

- Model, BOTH arms: `huihui_ai/qwen3-abliterated:8b` (Ollama). CAVEAT,
  recorded: this is a community abliterated variant already on disk; the
  official `qwen3:8b` could not be pulled (data volume at 99%, pull failed
  ENOSPC). Internally valid (same weights both arms); a rerun with official
  weights is a --model flag away once disk exists.
- Serving: isolated `ollama serve` at 127.0.0.1:11500 owned by this
  experiment (OLLAMA_CONTEXT_LENGTH=8192, OLLAMA_KV_CACHE_TYPE=q8_0,
  OLLAMA_FLASH_ATTENTION=1, OLLAMA_KEEP_ALIVE=45m). The shared instance at
  :11434 is not touched. Rationale: `ollama create`-derived models silently
  lose tool templating , and the shared server's default
  4096 context front-truncates agentic episodes.
- Verifier, BOTH arms: `verifier.test_runner.run_tests(code, tests,
  timeout_seconds=30)` -- an earlier decision record hardened runner -- executed OUTSIDE the
  agent workspace on the hidden `test_solution.py`. all_passed is the only
  success criterion.

## Suite (frozen)

The three blind banks, n = 98 tasks:
- `bank_alg` (20)
- `bank_mbpp` (50)
- `bank_physics` (28)

The runner writes `tasks-manifest.json` (task_id + README sha256 + tests
sha256) before episode 1; that manifest is the frozen suite of record.
Order: single shuffle, seed 42. Per task: arm A then arm B, back-to-back
(same-condition-does-not-replicate law; pairing absorbs shared drift).

## Arm A -- single-shot (the single-shot convention)

- POST /api/chat on :11500, `think: false`, `temperature 0.0`,
  `num_predict 2048`.
- Prompt: `build_solution_prompt(README)` (unchanged).
- `extract_code` -> verifier. CritiqueError (no code
  block) = fail (capacity, same as always).
- Registered confound, stated: arm A runs greedy (the strongest single-shot
  convention); arm B runs at dsh/model default sampling (temp 0.6). The
  treatment is "each harness as practiced", not a sampling study.

## Arm B -- dsh minimal agent

- deepseek-harness-sdk 0.1.1rc1 (venv `<venv>`), composition
  `scripts/composition-b1.yml` (sha256 recorded in the run
  header; thinking disabled, reasoningEffort off, bash + editor only).
- Fresh disposable workspace per task containing ONLY `README.md`. The
  hidden tests, gold.py, bad.py, metadata.json are NEVER in the workspace.
- Prompt template (frozen):

      You are solving a self-contained coding task inside the workspace
      directory {ws} (your bash shell starts there).

      The task specification:
      ---
      {readme}
      ---

      Requirements:
      - Create the solution at {ws}/solution.py, exactly matching the
        specified function signature.
      - You may write and run your own tests using bash (python3 is
        available). The hidden grading tests are not accessible to you.
      - Use absolute paths with the editor tool. When writing files, write
        real newline characters, never literal \n escape sequences.
      - When the file is written and verified, reply DONE.

- Session id `dsh1-{task_id}-a{attempt}` (unique per attempt; the
  retry-under-skip-key law).
- Caps (capacity rules, not excluded): episode wall-clock 600 s (subprocess
  process-group kill); per-request max_tokens 4096. AMENDED PRE-RUN
  2026-08-22 (before any scored episode, audit pass): a wall-cap
  kill terminates the episode and the candidate PRESENT at termination is
  graded (timed-exam rule); solution.py absent or empty at episode end =
  arm-B fail.
- Candidate = bytes of `{ws}/solution.py` after the episode, regardless of
  the agent's final message. Scored by the same verifier call as arm A.

## Anti-gaming audit (armed, )

dsh's bash is not path-jailed. After every arm-B episode the runner scans the
session JSONL tool stream. AMENDED PRE-RUN 2026-08-22 (before any scored episode): the agent naming its
OWN files `test_solution.py` (or writing its own tests) inside its workspace
is innocent and must not convict. Conviction (DISQUALIFIED, scored fail,
flagged) only on references to the repository: `<path>`,
`bank_alg`, or `records/experiments` in any tool-call argument. Bare
mentions of `test_solution`/`gold.py`/`bad.py` are recorded as review notes,
never convictions. Both detector directions are canaried before the campaign
(a planted repo-path probe must flag; an innocent own-test episode must not).
Zero convictions expected; the trap exists so silence means something.

## Infrastructure-failure policy (transient-error law)

The box is contended (a neighbor VLM service Metal-OOMed repeatedly tonight;
poisoned llama-server backends return empty/degenerate responses).

- Infra failure signatures: provider error (STREAM_CLOSED etc.), degenerate
  response (empty content + 0 usage tokens), HTTP/transport error, or arm-A
  empty reply. These are NEVER scored.
- On infra failure: `ollama stop` the model on :11500 (recreates the poisoned
  Metal backend), wait 20 s, retry the SAME arm; up to 2 retries per arm per
  task. Still failing => the whole PAIR is recorded UNKNOWN/excluded and
  reported. Wall-cap kills and CritiqueError are NOT infra failures.
- Campaign halt: >15 UNKNOWN pairs => environment too hostile; stop, report,
  reschedule. (Guards count consecutive... this one counts total because each
  exclusion permanently costs n; 15 ~= the power margin.)
- Per-episode context recorded: timestamp, wall seconds, retries, memory-free
  %, model calls, output tokens.

## Endpoints

- PRIMARY: paired task-level solved/failed; McNemar exact, two-sided
  binomial on discordant pairs, alpha 0.05.
- Secondary (descriptive, registered): per-arm Wilson 95% CIs; per-bank
  breakdown; cost per solve (wall s, model calls, output tokens); arm-B
  failure taxonomy (syntax-invalid solution.py vs wrong-logic vs cap-hit vs
  no-file); arm-B step-count histogram.
- Power, stated honestly: n=98. If ~20 pairs are discordant, a 15:5 split
  reaches p~=0.041; a 14:6 split does not (p~=0.115). Smaller true effects
  will be reported as counts + CI, not as a verdict (underpowered does not mean negative).

## Stops / verdict discipline

- Verdict computed only by the paired-test procedure over the per-task JSONL;
  no eyeballing.
- Any post-registration change to prompts, caps, model, or suite = a written
  amendment in this file BEFORE the affected episodes run; outcome-based
  voiding is forbidden.
- Publication of any kind goes through the go-public gate (the author review).

## AMENDMENT 2026-08-23 (pre-verdict, mechanism-driven): think-channel burn

Discovered from transcript inspection of run r1 (5 scored pairs), not from
outcomes: every failed arm-B episode showed 0 tool calls with the full 4096
max_tokens consumed and ZERO visible output. Root cause, verified by direct
probes: Ollama /v1 ignores both `thinking: {type: disabled}` and
`reasoning_effort: "off"` (the wire values the registered composition
produced) but honors `reasoning_effort: "none"`; qwen3 therefore reasoned
invisibly (dsh's adapter reads DeepSeek's `reasoning_content`, Ollama emits
`reasoning`) until the token cap. The registered condition "thinking
disabled" was NOT being delivered; hard tasks were scored against a
scaffold that never got to act.

Fix (composition, sha changes recorded in r2's run header): model catalog
entry maps reasoningEffort level `low` to wire value `none`
(`reasoningEfforts: {low: none}`), defaults `reasoningEffort: low`;
verified by probe (episode completes, tool calls flow, reasoning_len 0).
contextWindow literal corrected 16384 -> 8192 to match the serving
instance.

Disposition: ALL r1 scored pairs (5: 3 concordant-pass, 2 concordant-fail,
0 discordant) and the pilot are VOIDED wholesale regardless of direction;
r1 archived as runs/r1-voided-thinkburn (evidence). Campaign restarts
fresh as r2 under the fixed composition; same frozen manifest, same seed.
`/no_think` soft-switch note: ineffective on this abliterated variant
(verified); the wire-level mapping is the only working control.

## AMENDMENT 2026-08-23b (pre-run): the 08-23a fix did NOT work; wire shim

The 08-23a amendment assumed dsh's per-model `reasoningEfforts` map would put
`none` on the wire. It does not. Ground truth, captured with a logging proxy
in front of the serving instance during a live episode, is that
`@deepseek-ai/dsh-llm-deepseek` sends:

    {"thinking": {"type": "enabled"}, "reasoning_effort": "low", ...}

i.e. its own level name, ignoring both `reasoningEfforts` and
`thinkingLevelMap` in the model entry (only the together/zai adapters honor
those, and neither ships in this bundled runtime). Measured Ollama behavior
for this model: `"off"` and `"minimal"` are rejected 400 (`must be "high",
"medium", "low", "none"`), `"low"`/`"medium"` leave thinking ON, and ONLY
`"none"` turns it off. dsh's enum has no `none`, so no composition can
express the registered condition. pilot2 accordingly still burned (2 of 3
episodes: 0 steps, 4096 tokens, 0 visible characters).

Fix, three parts, all probe-verified before any scored episode:

1. `scripts/dsh/dsh1_shim.py` -- a 120-line passthrough on 127.0.0.1:11502
   that rewrites exactly two request fields (`reasoning_effort` -> `"none"`,
   drop `thinking`) and streams everything else unchanged. Arm B's episodes
   now point at the shim; arm A keeps using native `/api/chat` with
   `think:false` on :11500 (verified unaffected). `--selftest` is a
   known-positive check: it sends the exact fields dsh sends and asserts the
   reply has content AND `reasoning_len == 0` (PASS recorded 2026-08-23).
2. Runner burn detector: an arm-B episode with 0 tool calls, 0 visible
   characters, and >= 95% of max_tokens consumed is raised as an InfraError,
   not scored. It retries under the existing infra policy and, if it
   persists, the PAIR becomes UNKNOWN. Rationale (transient-error law): a
   model reasoning into a channel the adapter cannot read is a serving
   defect; it is not evidence about the scaffold in either direction.
3. Supervisor gates hardened: the warm probe now goes THROUGH the shim using
   dsh's exact fields and asserts both directions (content present AND
   thinking off), so a dead shim or a regressed serving path fails the gate
   instead of starting a campaign. The pilot gate now fails on ANY unknown
   pair or ANY dead (0-step, non-cap) arm-B episode; the previous gate
   passed on 1-of-3 agents alive, which is precisely how a broken path
   reached the campaign.

Disposition: pilot2 and the r2 attempt (1 pair, never written) are voided;
r1 remains voided. The campaign runs as r3 -- same frozen manifest, same
seed 42, same 98 tasks, no change to prompts, caps, model, verifier, or
endpoints. Recorded honestly: three launches were needed to deliver the
registered condition, and the defect was found by transcript audit
(out_tokens vs visible characters), not by any outcome looking wrong.

## AMENDMENT 2026-08-23c (pre-run): unauditable episodes are never scored

pilot3 ran on the shimmed path and produced candidates (one solved), but
every episode reported steps=0 / out_tokens=0. Cause: pilot3 was launched
with a RELATIVE `--run-dir`, and the SDK resolves a relative session_root
against the agent's workspace -- so transcripts were written inside the
disposable workspace and deleted with it. Nothing errored; the pairs simply
became blind. The hardened 08-23b pilot gate DID catch it (all three
episodes read as dead -> FAIL), which is the gate working as intended.

Two fixes, both canaried:
1. The runner resolves `--run-dir` to an absolute path at startup.
2. A missing transcript is now an InfraError, never a score. Without the
   JSONL the anti-gaming scan and the burn detector are both blind, and a
   blind detector reporting "no convictions" is exactly the silence
   the audit forbids.

pilot3 archived as pilot3-voided-blind-instrumentation. Pilot rerun as
pilot4 (absolute path). No change to the frozen suite, prompts, caps, model,
verifier, or endpoints.

## AMENDMENT 2026-08-23d (pre-run): arm-A guard, cause-split unknowns, short workspace

Three changes, all made before any scored episode, after an advisor review
and a one-pair smoke test. Nothing about the suite, the seed, the model, the
verifier, or the endpoints changes.

1. ARM A WAS UNGUARDED. All of the 08-23a..c work hardened arm B; arm A
   still had no token accounting and no transcript, so it could produce
   unauditable data points while arm B could not -- an asymmetry the verdict
   could not survive. Probed directly: `/api/chat` with `think:false` on this
   model returns `thinking` empty and `eval_count` ~107 on a task README, so
   the control does work. Guard added anyway: every arm-A episode now records
   `eval_count`, `done_reason`, and `thinking_len`, and ANY leaked thinking
   raises a config-class InfraError. Deliberately NOT treated as infra:
   exhausting `num_predict` with thinking verified off and no fenced block --
   that is a real failure of the single-shot convention and is scored as one.

2. UNKNOWNS ARE SPLIT BY CAUSE. InfraError now carries kind=config (thinking
   leaked, think-burn, missing transcript -- the registered condition was not
   delivered) or kind=env (provider/transport/OOM/degenerate -- the contended
   box). The cause is recorded on every UNKNOWN pair. The pilot gate blocks on
   config-class unknowns only; blocking on env-class ones would have
   deadlocked the launch forever, since the neighbor VLM service can Metal-OOM
   at any moment and the campaign itself already tolerates 15 such exclusions.
   Pilot limit raised 3 -> 5 for the same reason: unknown pairs are never
   re-run on resume, so ">= 2 scored" must stay reachable.

3. THE WORKSPACE PATH WAS THE WRONG EXPERIMENT. Smoke test on
   D-008-isqrt-newton: the agent spent all 16 of its turns re-issuing the same
   `create` and failing with `EACCES: permission denied, mkdir
   '/private/var/folders/cl/kqw_2w_j2gd0_h000fq_tbggr0000gn'` -- it had
   mistyped one character of the 60-char random tmpdir, so the editor tried to
   create a new directory under a system path. Arm B was being scored on
   its ability to transcribe a random path, not on coding. Workspaces are now
   `/tmp/dsh1ws/<task_id>` (short, meaningful, cleaned per attempt), `DSH_CWD`
   is set so the bare name `solution.py` also resolves, and the prompt says
   both forms work. Per-episode `tool_errors` is now recorded so any residual
   path friction is visible in the report rather than silently costing arm B.
   Re-smoke-tested on the same task: 54 steps, 1 tool error, candidate written,
   107/109 hidden tests passing (vs arm A's 104/109). Both arms still fail the
   task -- the point is that the failure is now the model's, not the harness's.

This is the fourth amendment and the fourth launch attempt. Every defect so
far was found by auditing mechanism (token accounting, wire capture,
transcript presence, tool-result errors), never by a result looking wrong.

## AMENDMENT 2026-08-23e (pre-run): transcripts must be provably this episode's

pilot4 passed its gate, and four of its five pairs are sound. The fifth
exposed a data-integrity bug that matters more than any result: for
D-008-isqrt-newton the runner attributed a transcript written at 18:55 by an
EARLIER, killed run (old long-tmpdir workspace, 6 EACCES turns) to a fresh
episode recorded at 19:25. dsh keys its session directory on the encoded
workspace path, so the same `session_id` used against two different
workspaces leaves two directories, and `hits[0]` picked arbitrarily. The
pair's step count, token count, and -- critically -- its anti-gaming scan
described a different episode entirely. (The fresh episode itself hit the
600 s cap and never produced a transcript, which is why the stale one was
the only match.)

Fixes:
1. `find_session_jsonl` now requires exactly ONE match, preferring the
   directory whose encoded path names this task's own `/tmp/dsh1ws/<task>`
   workspace. Zero or ambiguous matches return None, which the 08-23c rule
   turns into a config-class InfraError -- unscoreable rather than silently
   wrong.
2. `dsh1_verdict.py` runs an ATTRIBUTION AUDIT over the finished run: every
   scored pair must map to exactly one own-task transcript, and any that does
   not is printed as MISATTRIBUTED before any number is believed. Verified as
   a known positive against pilot4: it reports 4/5 and names D-008.

r3 had recorded ZERO pairs when this was found, so it is being restarted from
scratch rather than patched mid-flight -- all 98 pairs will run under one
code version. pilot4 is kept as-is (a wiring check, excluded from analysis);
its D-008 metrics are known bad and are not used for anything. The stale
transcript is deliberately NOT deleted: it is the evidence.

## INTERPRETATION PRE-COMMITMENT (written at 29/98, before the result is in)

Interim state, recorded so the reading of the final numbers cannot be fitted
to them after the fact: A=21 B=13 of 29 scored, discordance entirely
one-directional (B-only=0, A-only=8), arm-B unsolved split 5 wall-cap /
4 syntax-invalid / 7 wrong-logic, cap_hit on 10 of 29 episodes (34%), mean
wall 21 s (A) vs 297 s (B).

How this will be reported whatever the endpoint says:

- If B < A significantly, the claim is NOT "agentic scaffolds are worse".
  It is: "under a 600 s per-episode budget, on this 98-task suite, with an
  8B local model, the dsh minimal agent solved fewer tasks than a
  single-shot generator, at ~14x the wall time." The budget is part of the
  treatment and must appear in the sentence.
- The cap rate is a first-class result, not a footnote. A third of episodes
  hitting the wall means the comparison is partly a budget comparison. The
  taxonomy (cap / syntax-invalid / no-file / wrong-logic) will be published
  with the verdict so a reader can see how much of the gap is "slower" and
  how much is "wronger".
- syntax-invalid candidates are counted as genuine arm-B failures: writing
  valid code through a tool call IS the scaffold's job. They are reported
  separately anyway, because they are the failure mode most likely to be
  model-scale-dependent.
- The obvious follow-up (larger cap, or cap normalised by tokens rather than
  seconds) is NOT run now and NOT used to discount this result. It would be a
  separately registered experiment.
- The 600 s cap, the greedy-vs-default sampling asymmetry, and the
  abliterated-variant model caveat are all pre-registered confounds and will
  be restated in the conclusion regardless of direction.

No parameter of the running campaign is changed by this note. Changing the
cap now, with arm B behind, would be exactly the outcome-driven amendment the
protocol forbids.
