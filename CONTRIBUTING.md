# Contributing

## Environment

- use the project virtual environment at `.venv/`
- target Python `3.12`
- prefer `/opt/homebrew/bin/python3.12` when recreating the environment locally

## Basic Workflow

Run tests before proposing changes:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Run the public repository audit before a public-facing commit:

```bash
.venv/bin/python scripts/audit_public_repo.py
```

## Public Commit Rules

- keep `upstream/mediacms` as a clean submodule reference only
- do not commit local edits inside `upstream/mediacms`
- do not commit `.agents/` contents
- do not commit benchmark artifacts from `runs/`
- do not commit local tool state such as `.qwen/`, `.playwright-cli/`, `.openclaw/`, `.hermes/`, or `.aider*`

Useful checks:

```bash
git status --short
git -C upstream/mediacms status --short --untracked-files=all
```

## Benchmark Notes

- benchmark results are local operational artifacts, not source files
- if a task changes visible UX/UI, Playwright verification is part of the benchmark acceptance flow
- keep third-party attribution current in `THIRD_PARTY.md` when adding shipped or referenced external components
