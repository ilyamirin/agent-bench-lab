# agent-bench-lab

![agent-bench-lab README hero](docs/assets/readme-hero-agent-bench-lab.png)

Public repository for the `coding-agents-comparison` benchmark harness for
comparing coding agents against the same Python project, task pack, and
verification flow.

## Status

This repository is a public prototype, not a finished product.

What is already in place:

- a Docker-based benchmark harness for `MediaCMS`
- a strict model policy around `OpenRouter / qwen/qwen3.6-plus`
- normalized run artifacts and cohort reporting
- automated acceptance plus mandatory Playwright checks for UI-touching tasks

What is still evolving:

- adapter coverage across all target agents
- browser-harness robustness across every agent/runtime combination
- task breadth beyond the first benchmark task

## Current Benchmark Snapshot

The benchmark has now produced two full end-to-end successes on
`simple_content_warning` under the shared `OpenRouter / qwen/qwen3.6-plus`
policy:

- `yulya-zig` is the current top result in the maintained harness
- `Qwen Code` remains the strongest external baseline

Several other agents reached meaningful partial implementations, but usually
fell short on closure: migrations, benchmark-safe targeted tests, visible UI
surfaces, or browser-level persistence verification.

Suggested repository social preview asset:
[social-preview-agent-bench-lab.png](docs/assets/social-preview-agent-bench-lab.png)

## What This Repository Ships

- benchmark harness code in `src/`
- tests in `tests/`
- benchmark task manifests in `benchmark/tasks/`
- benchmark and design docs in `docs/`
- a git submodule reference to `MediaCMS` at `upstream/mediacms`

What this repository does **not** ship:

- local agent clones under `.agents/`
- benchmark run outputs under `runs/`
- local tool state such as `.qwen/`, `.openclaw/`, `.hermes/`, `.playwright-cli/`, or `.aider*`

## Benchmark Scope

The current benchmark prototype compares coding agents on a shared `MediaCMS`
baseline with:

- one benchmark target app: `MediaCMS`
- one locked provider/model policy: `OpenRouter / qwen/qwen3.6-plus`
- one current public task pack centered on `simple_content_warning`
- automated acceptance checks and browser-level verification when a task changes visible UX/UI

Design and benchmark specs:

- [2026-04-21 MediaCMS Benchmark Plan](docs/superpowers/specs/2026-04-21-mediacms-benchmark-plan.md)

Latest detailed benchmark analysis:

- [Forensic Report for `simple_content_warning`](docs/simple_content_warning_forensic_report.en.md)

## Setup

Use the project virtual environment only:

```bash
source .venv/bin/activate
python --version
```

Expected version:

```bash
Python 3.12.x
```

If you need to recreate the environment:

```bash
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
```

## Running Checks

Run the unit tests:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Run the public repository audit:

```bash
.venv/bin/python scripts/audit_public_repo.py
```

## Running a Benchmark Attempt

The current CLI entrypoint is the benchmark cohort runner:

```bash
PYTHONPATH=src .venv/bin/python -m benchmark_lab --agents qwen-code --attempts 1
```

For a single agent and single attempt without cohort aggregation:

```bash
PYTHONPATH=src .venv/bin/python -m benchmark_lab.single_run --agent yulya-zig --attempt 22
```

The runner now performs an early Docker access preflight. If `docker ps` is not
available from the runner process, the attempt exits early as `infra_error`
instead of failing later during environment boot.

This writes local-only artifacts under `runs/`. Those artifacts are part of the
local evaluation workflow and are intentionally not versioned.

## Public Commit Rules

- keep `upstream/mediacms` as a clean submodule reference
- do not commit local changes inside the submodule
- do not commit `.agents/` contents
- do not commit raw benchmark artifacts from `runs/`
- keep local tool state out of public commits

Before a public push, check both:

```bash
git status --short
git -C upstream/mediacms status --short --untracked-files=all
```

## License and Third-Party Components

The benchmark harness code in this repository is licensed under `MIT`:
[LICENSE](LICENSE)

`MediaCMS` is an external upstream submodule from
[mediacms-io/mediacms](https://github.com/mediacms-io/mediacms.git) and keeps
its own `AGPL-3.0` license. If you use the submodule, you need to review and
comply with MediaCMS licensing separately from this repository.

The full third-party inventory, upstream URLs, and license notes are documented
in [THIRD_PARTY.md](THIRD_PARTY.md).

## Current Local Agent Set

The local comparison corpus currently targets:

1. `Hermes Agent`
2. `Kilo Code`
3. `OpenCode`
4. `Cline`
5. `Qwen Code`
6. `OpenHands`
7. `Codebuff`
8. `Crush`
9. `Aider`
10. `OpenClaw`
11. `NullClaw`
12. `Pi`
13. `yulya-zig`

These are local-only optional benchmark targets. Their upstream URLs and
licenses are documented in [THIRD_PARTY.md](THIRD_PARTY.md).

## Native Agent Development

`yulya-zig` is the in-repo headless benchmark agent implemented in Zig.

Current role:

- benchmark-first agent optimized for acceptance-driven coding tasks
- current top result on `simple_content_warning`

Build:

```bash
cd native/yulya-zig
zig build -Doptimize=ReleaseSafe
```

Doctor:

```bash
native/yulya-zig/zig-out/bin/yulya-zig doctor --workspace upstream/mediacms
```
