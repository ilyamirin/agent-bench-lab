# Project Scaffold Design

Date: 2026-04-21

## Goal

Create the initial repository scaffold for a Python 3.12 project used to compare different coding agents.

## Decisions

- Initialize a git repository in the current directory.
- Use the local Homebrew Python at `/opt/homebrew/bin/python3.12`.
- Create the project virtual environment in `.venv/`.
- Reserve `.agents/` for local agent implementations and ignore it in git.
- Add `README.md` and `AGENTS.md` at the repository root.
- Start with a lightweight structure: `src/`, `tests/`, `.agents/`, `docs/`.

## Non-Goals

- No application logic yet.
- No CI, linting, formatting, or test tooling yet.
- No tracked agent implementations yet.
