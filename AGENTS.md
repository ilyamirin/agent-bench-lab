# AGENTS.md

## Purpose

This repository is used to compare different coding agents in a shared Python project.

## Environment Rules

- Use only the project virtual environment at `.venv/`.
- Target Python `3.12`.
- Prefer `/opt/homebrew/bin/python3.12` when recreating the environment.

## Repository Conventions

- Keep agent-specific local artifacts inside `.agents/`.
- Treat `.agents/` as local-only and do not rely on git-tracked contents there.
- Put reusable project code in `src/`.
- Put tests in `tests/`.
- Document significant setup or workflow decisions in `README.md` or `docs/`.

## Current Agent Set

The local comparison corpus in `.agents/` currently includes:

1. `Hermes Agent` -> `.agents/hermes-agent`
2. `Kilo Code` -> `.agents/kilocode`
3. `OpenCode` -> `.agents/opencode`
4. `Cline` -> `.agents/cline`
5. `Qwen Code` -> `.agents/qwen-code`
6. `OpenHands` -> `.agents/openhands`
7. `Codebuff` -> `.agents/codebuff`
8. `Crush` -> `.agents/crush`
9. `Aider` -> `.agents/aider`
10. `OpenClaw` -> `.agents/openclaw`
11. `NullClaw` -> `.agents/nullclaw`
12. `Pi` -> `.agents/pi`
13. `yulya-zig` -> `native/yulya-zig`

## Replacement Notes

- `Claude Code` was intentionally replaced with `OpenCode`.
- `BLACKBOXAI` was intentionally replaced with `Aider`.
- `Slate Agent` was intentionally replaced with `OpenClaw`.
- The replacement set reflects the current public repositories available for cloning into `.agents/`.

## Benchmark Verification

- Record benchmark results under `runs/` with normalized artifacts such as `result.json`, `summary.md`, and visual reports when available.
- Always run automated acceptance checks for the task before considering a benchmark attempt successful.
- If a task changes UX/UI or any visible product surface, a browser-level check is mandatory.
- Use Playwright for that browser-level verification and capture what was observed in the run results.

## Safety

- Do not remove or overwrite unrelated user changes.
- Keep the initial repository structure simple unless explicitly asked to expand it.
