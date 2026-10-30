# Crutch

**An Agent Scaffold Did Not Beat a Single Sampled Answer at 14B or 32B: Pre-Registered Tests of DeepSeek Harness 0.1.1rc1 with Open Qwen3 Models**

Four pre-registered experiments on whether an agent harness helps a small local
model solve programming tasks. Read the paper at `paper/paper.pdf`, or as
Markdown at `paper/paper.md`.

## Rebuild

Tables and the paper text need only the Python standard library.

    make paper       # data/ -> tables -> paper/paper.md
    make figures     # data/ -> six SVG figures (needs matplotlib)
    make pdf         # paper.md -> paper.pdf (needs pandoc and Chrome)

## Layout

- `data/` per-task outcomes for every arm of every experiment
- `protocols/` the pre-registered protocols and their dated amendments
- `paper/` the paper, its generated tables and figures, and the rendered PDF
- `scripts/` the table, figure, paper and PDF builders

Raw agent transcripts are not included.

## Choices made on the author's behalf, open to change at review

- The cluster is described only as an academic HPC cluster, with no institution named.
- The protocols are kept, with references to other work replaced by neutral wording.
- Code is MIT licensed (`LICENSE`). The paper text and figures are CC BY 4.0 (`LICENSE-PAPER`).
- The repository is named Crutch.

## Scope

Results apply to harness version 0.1.1rc1 driving open Qwen3 models of 8B, 14B and
32B parameters through a local request-rewriting proxy. They do not apply to the
native DeepSeek models or to the 0.2 releases of the harness.
