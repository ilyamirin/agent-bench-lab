# MediaCMS Headless Agent Benchmark Plan

Date: 2026-04-21

## Summary

Build a reproducible benchmark lab around `mediacms-io/mediacms` for comparing coding agents in headless mode.

The benchmark must measure four axes:

1. `task solved`
2. `reliability`
3. `quality`
4. `speed/cost`

The benchmark will use:

- a moderate benchmark adaptation of `MediaCMS`
- Docker-only execution
- local deterministic `micro-staging` instead of real external services
- a hybrid runner model with native per-agent adapters and a shared run contract
- full reset on every `agent x task x attempt`
- `3` independent attempts per task
- hybrid acceptance: mandatory automated checks plus manual review
- tabular reports plus radar charts per agent

## Locked Decisions

### Project and Execution

- Base project: `MediaCMS`
- Adaptation style: moderate benchmark adaptation
- Execution environment: Docker only
- Isolation policy: full reset on every run
- External integrations: local `micro-staging` only
- Agent execution model: hybrid
- Attempts per task: `3`

### Model Policy

- Provider: `OpenRouter`
- Model: `qwen/qwen3.6-plus`
- Compatibility policy: `Strict`
- Generation policy: `Model strict, agent default`

This means:

- every benchmarked agent must use `OpenRouter / qwen/qwen3.6-plus`
- no shim, proxy, monkeypatch, request rewrite, or patched transport layer is allowed
- no model fallback is allowed
- if an agent cannot natively support this provider/model setup, it is marked `incompatible`
- provider and model are fixed across agents
- other generation settings remain the agent's native defaults unless the agent requires explicit values to start

## Benchmark Architecture

### Repository Areas

- `upstream/mediacms/` — MediaCMS baseline used for benchmark runs
- `benchmark/tasks/` — task manifests, prompts, limits, acceptance contracts
- `benchmark/runners/` — shared runner contract plus per-agent adapters
- `benchmark/microstaging/` — local external-service simulators for the hard task
- `benchmark/scoring/` — automated checks, score calculation, manual-review rubric
- `benchmark/reports/` — leaderboard, summaries, radar chart generation
- `benchmark/seeds/` — deterministic fixtures and initial state
- `docker/` — Dockerfiles, compose files, reset/run orchestration
- `runs/` — logs, diffs, metrics, scores, manual review notes

### Docker Stack Per Run

Each isolated run uses a fresh Docker stack with:

- `app` — MediaCMS application
- `db` — Postgres
- `worker` — background jobs
- optional runtime/frontend service if required by MediaCMS setup
- `runner` — benchmark orchestration
- `judge` — automated verification
- `micro-staging-*` — deterministic local external services

### Run Contract

Every run uses one normalized contract.

Input:

- `agent_id`
- `task_id`
- `attempt`
- time/resource limits

Execution steps:

1. create a fresh workspace snapshot
2. bring up a fresh Docker stack
3. run compatibility preflight for provider/model support
4. inject task instructions through the agent's native adapter
5. wait for completion or timeout
6. collect logs, patch/diff, and check results
7. tear down containers, volumes, and temp state completely

Output:

- normalized JSON result
- stdout/stderr
- runtime metrics
- exit code
- patch/diff
- automated-check results
- manual-review record
- final per-axis scores
- actual provider/model configuration used

## Compatibility Rules

### Compatible Agent

An agent is benchmark-eligible only if it can natively:

- accept a custom API key
- accept an OpenRouter endpoint or native OpenRouter provider mode
- accept the exact model id `qwen/qwen3.6-plus`
- run without source patches to the agent itself
- run without an intermediate compatibility wrapper

Allowed:

- documented env vars
- documented CLI flags
- documented config files
- documented provider selection

Forbidden:

- local proxy rewriting requests
- adapter-level request schema transformation
- source patching the agent to add provider support
- silently changing to another model
- compatibility shim of any kind

### Incompatible Agent

Mark an agent `incompatible` if:

- OpenRouter cannot be configured natively
- the exact model id cannot be configured
- the agent requires a shim or undocumented workaround
- the agent is vendor-locked
- the agent silently substitutes another model

Incompatible agents are reported separately and do not enter task execution.

## Benchmark Tasks

### 1. Simple

Add a new media metadata field, for example `content_warning`, and carry it through:

- model
- API
- validation
- one visible product surface
- targeted tests

Purpose:

- small but real atomic task
- checks whether the agent can follow an existing data flow cleanly

### 2. Medium

Add a scheduled-publication guard:

- scheduled content must not auto-publish unless moderation status is valid
- required metadata must be present

This task should touch:

- domain/business logic
- worker path
- API behavior
- user-visible status or error output
- integration and regression tests

### 3. Hard

Add an external-review pipeline for premium content:

- transition to `ready_for_review`
- call local moderation micro-staging
- call local enrichment micro-staging
- call local notification micro-staging
- only after successful completion allow transition to `approved_for_publish`

This task must cover:

- workflow/state transitions
- orchestration service
- background jobs
- API/admin action flow
- visible status in UI or API
- retries/idempotency
- end-to-end checks against local micro-staging

## Acceptance and Scoring

### Acceptance Layers

Every task result is judged through three layers:

1. execution outcome
2. automated acceptance
3. manual review

### Scoring Axes

Each task is scored `0-4` on:

- `task solved`
- `reliability`
- `quality`
- `speed/cost`

Interpretation:

- `task solved` — degree to which the task is actually completed
- `reliability` — consistency across all `3` attempts
- `quality` — architecture fit, regressions, test adequacy, correctness
- `speed/cost` — runtime and other available resource signals

### Manual Review

Manual review is part of the benchmark by design.

- one manual review is performed on the best completed attempt for each `agent x task`
- reliability uses all `3` attempts
- the rubric must stay fixed once benchmark execution begins

### Reporting

The reporting layer must generate:

- leaderboard table
- per-agent summary card
- per-task breakdown
- links to run artifacts
- radar charts for each agent on the `4` scoring axes
- radar charts per task and for aggregate agent profile

## Delivery Order

### v1 Minimal Harness

First milestone:

- Dockerized MediaCMS baseline
- full reset working reliably
- one working task
- one working agent adapter
- one normalized result JSON
- one generated report with radar chart

### Recommended Implementation Sequence

1. build the Docker baseline and verify reset reproducibility
2. define the shared run contract and result schema
3. implement compatibility preflight for provider/model policy
4. encode the three tasks as manifests with acceptance checks
5. add `2-3` proof-of-concept agent adapters
6. implement scoring and manual review rubric
7. add deterministic micro-staging services
8. add reports and radar charts
9. expand to all collected agents

## Explicit Non-Goals for Early Iterations

- no real external API integrations
- no immediate support for all `10` agents before the harness is stable
- no collapsing everything into one magic benchmark score
- no starting with the hard task before simple and medium are stable
