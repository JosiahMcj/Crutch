# DSH-3: does the agentic deficit shrink with model scale, and how much does it vary?

Registered 2026-09-21, BEFORE any scored episode. Follow-up to DSH-1
an earlier experiment and DSH-2. Runs on **the cluster** (an academic HPC cluster), not the Mac.

## The two open questions, answered in one design

1. **Scale.** DSH-1/2 were entirely at 8B. The registered confound was that
   the agent's binding constraint (non-convergence inside its budget) is
   exactly what should improve with capability. Rungs: **qwen3:8b, 14b, 32b**
   -- one dense family, official weights.
2. **Variance.** DSH-2 showed the agentic arm swings across sessions
   (23->32/48) while greedy single-shot is exact (0/48 flips). The registered
   fix was "report the distribution of the gap, not one p-value". Each rung
   runs **3 independent agent sessions**.

## Hardware and serving (new, and it matters)

- One **exclusively allocated** GPU node (4x NVIDIA A30, 24GB VRAM each,
  64 cores, 512GB RAM). Exclusive because the treatment IS a 600 s wall cap:
  a co-tenant stealing GPU time would corrupt the measurement
  ().
- Ollama 0.34.2 static build from /scratch, **`OLLAMA_LLM_LIBRARY=cuda_v12`**
  -- the cuda_v13 path hangs forever at model warmup on Ampere
  (). Verified genuinely on GPU:
  84 tok/s and 11.2GB VRAM resident, vs 14.3 tok/s and 0MiB on CPU.
- `OLLAMA_CONTEXT_LENGTH=8192`, wire shim forcing `reasoning_effort: none`
  -- both identical to DSH-1/2.
- **The abliterated-variant caveat is GONE**: official `qwen3:*` weights,
  since egress and disk now permit it. This is a deliberate improvement over
  DSH-1 and means DSH-3 is NOT a like-for-like replication of it.

## Suite

The same frozen 98 tasks (blind_holdout 20 + mbpp_blind 50 + physics_blind
28), manifest re-verified by sha on the cluster before episode 1. Seed 42.

## Arms per rung

- **A (single-shot)**: `build_solution_prompt`, think:false, temp 0.0,
  num_predict 2048. Run **once per rung**, because DSH-2 measured it exact
  across sessions (0 of 48 tasks changed). **That determinism is re-verified
  on the cluster before it is relied on** -- arm A is run twice on a 12-task probe
  and must agree 12/12, else it is run per-session like B.
- **B (dsh minimal agent)**: unchanged composition and prompt, 600 s wall
  cap, max_tokens 4096. **3 independent sessions per rung**, one per GPU,
  concurrently on the one exclusive node. Independent = separate ollama
  server, separate model instance, separate process, separate sampling
  stream.

## Endpoints

- PRIMARY, per rung: paired A-vs-B solved/failed, McNemar exact two-sided,
  alpha 0.05, using session 1 of B. Power lives in the discordant count and
  that count is reported with every p-value.
- PRIMARY, across rungs: the A-minus-B gap at 8b / 14b / 32b. The scale
  question is whether that gap shrinks monotonically.
- SECONDARY: the **distribution** of the gap over the 3 sessions per rung
  (this is DSH-2's registered follow-up); per-session solve counts;
  syntax-invalid, no-file, cap-hit and wrong-logic taxonomy per arm per rung;
  steps, wall seconds, output tokens, tool errors.

## Named confound, with its reading pre-committed

**The wall cap is not scale-neutral.** 600 s buys fewer agent steps at 32b
than at 8b, so a "scale effect" could be a budget effect wearing a costume.
Pre-committed reading, written before any rung is run:
- If cap-hit rates are comparable across rungs, the gap movement is a scale
  effect.
- If the 32b cap-hit rate is materially higher, the cross-rung comparison is
  budget-confounded and will be REPORTED AS SUCH, not as a scale result. In
  that case the honest statement is about tokens-to-solution, which is
  recorded per episode for exactly this purpose.
- The cap is NOT changed mid-program to rescue any rung.

Also carried forward from DSH-1: arm A greedy vs arm B default sampling is
"each harness as practiced", not a sampling study.

## Independence caveat, stated up front

The 3 sessions per rung run CONCURRENTLY on one node, so they measure the
scaffold's **sampling** stochasticity. They do NOT measure temporal drift
(DSH-2's 3-days-apart effect), which may include server or model state.
Claims will say "across independent concurrent sessions", never "across
days".

## Inherited infrastructure (reused unchanged)

Wire shim, think-burn detector, transcript attribution guard,
missing/ambiguous transcript => unscoreable, env-vs-config unknown split,
absolute run-dir, KILL lever, torn-record tolerance, the anti-gaming scan
(now keyed to the cluster checkout path). All canaries re-run green after the
portability edit.

## Data custody (user requirement)

Nothing is stored on compute nodes. Model weights live in a /scratch cache
(re-downloadable, not data). **Every pair record and transcript is rsynced
back to the Mac and verified as a strict superset before the next rung
starts** -- .

## Stops

- Known-positive before the campaign: one live agent episode on the cluster must
  show tool calls and a compilable file.
- Arm A determinism probe must pass 12/12 or the design changes to
  per-session A.
- Verdict by the paired-test procedure only.
- Post-registration changes require a written amendment BEFORE the affected
  episodes. Outcome-based voiding is forbidden.

## Design note added pre-run: arms run concurrently, not sequentially

DSH-1 ran arm A then arm B back-to-back per task, to stop session drift from
separating the arms. On the cluster, arm A (GPU 0) and the three arm-B sessions
(GPUs 1-3) run in the SAME time window on the SAME exclusive node. That
serves the same purpose at least as well -- the arms share one time window
rather than alternating through it -- and is recorded here rather than
discovered later. Each GPU hosts its own ollama server and (for B) its own
wire shim, so the arms never share a server queue.

## PRE-COMMITMENT written 2026-09-21 after 8b+14b, BEFORE 32b finishes

Two rungs are in and the gap has collapsed (8b mean +18.3, all p<0.001;
14b mean +1.7, all p>0.68). 32b is still running. How the third point will
be read, fixed now so it cannot be fitted to whatever arrives:

- **Gap stays ~0 at 32b** -> the ladder is monotone and the honest claim is
  "the 8B agentic deficit is a small-model effect; by 14B the scaffold is at
  PARITY". Parity, not benefit -- it still costs ~15x the wall time, so the
  engineering decision to keep baseline single-shot stands on COST, while
  DSH-1's stated reason (the scaffold makes the model worse) is retired
  above 8B.
- **Gap reopens at 32b** -> non-monotone, and I will NOT tell a story about
  it. The report will say the ladder is non-monotone, give all three points,
  and name the most likely artifact (32b is slower, so the fixed 600 s cap
  buys fewer steps -- check cap-hit rate first: 8b was 11-14/98, 14b 0-3/98).
- **Agent BEATS single-shot at 32b** -> the first evidence in this program of
  a scaffold adding capability, and it would need replication before it is
  claimed. It would be reported as "one rung, three sessions, needs a second
  independent run", not as a promotion.

Registered secondary already predicted and confirmed at 14b: the two failure
modes DSH-1/2 identified (syntax-invalid files, cap-hits) collapse together
with the gap -- 15-17 -> 1-3 and 11-14 -> 0-3. Whatever 32b shows, that
co-movement is the mechanism evidence and will be reported.
