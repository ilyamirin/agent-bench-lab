# Forensic Report for `simple_content_warning`

This is the public-safe version of the task 1 forensic report.

It keeps the main conclusions from the current cohort while intentionally
omitting raw local artifacts, unpublished run logs, and local-only workspace
references.

## What The Task Required

The benchmark task asked agents to add `content_warning` support to the
`MediaCMS` stack end-to-end:

- extend the model and serializer/API contract
- wire at least one visible product surface
- add targeted tests that match benchmark acceptance
- survive automated checks and browser-level verification

That is why many plausible-looking patches still counted as failures.

## Cohort Outcome

- `Qwen Code` produced the only end-to-end success in the current cohort.
- Several agents produced real partial implementations.
- `Pi` was successfully admitted as a native npm CLI benchmark target and
  reached a clean, meaningful benchmark run.
- `NullClaw` was successfully admitted as a Docker/OCI benchmark target and
  reached real code generation, but its best run still failed acceptance.
- The dominant failure mode was not “no code,” but failure to close the full
  implementation-and-verification loop.

## Main Failure Patterns

### Incomplete closure

Many agents edited the right parts of the stack, but stopped short of a full
benchmark-valid result.

### Weak self-verification

Several runs ended with optimistic completion summaries even when the resulting
workspace still failed targeted benchmark checks.

### Backend-first bias

Some agents reached a coherent backend slice but still failed visible-surface
completion or browser-level verification.

### Drift from the benchmark contract

In several partial runs, the agent solved a nearby problem rather than the
exact task the benchmark specified.

### Execution still matters after admission

`NullClaw` adds a useful new contrast case: an agent can be fully runnable
through OCI, can edit the right files, and still fail because the run never
produces a benchmark-safe final state.

## Why `Qwen Code` Won

`Qwen Code` stood out because it closed the full path:

- required code changes were made across the needed layers
- the benchmark-targeted checks passed
- the visible product path survived browser verification

The key differentiator was operational completeness, not just plausible code.

## Public Takeaway

This benchmark is most useful when read as a test of closure discipline:

- can the agent understand the codebase
- can it make the needed changes
- can it verify those changes in the right environment
- can it finish the real loop instead of stopping at a good-looking patch

## `NullClaw` Snapshot

`NullClaw` is now part of the local corpus as an OCI-backed agent. Its first
meaningful benchmark run was
[attempt-2](../runs/nullclaw__simple_content_warning__attempt-2/result.json).
That run passed environment boot and produced real edits across the model,
serializers, form, and a migration, but it still failed the benchmark because
no targeted `content_warning` test file was created, the contract check failed,
UI wiring stayed incomplete, and the run did not terminate cleanly.

Relevant local artifacts:

- [result.json](../runs/nullclaw__simple_content_warning__attempt-2/result.json)
- [changes.patch](../runs/nullclaw__simple_content_warning__attempt-2/changes.patch)
- [stdout.log](../runs/nullclaw__simple_content_warning__attempt-2/stdout.log)
- [targeted_tests.json](../runs/nullclaw__simple_content_warning__attempt-2/checks/targeted_tests.json)
- [contract_shell.json](../runs/nullclaw__simple_content_warning__attempt-2/checks/contract_shell.json)
- [ui_wiring_static.json](../runs/nullclaw__simple_content_warning__attempt-2/checks/ui_wiring_static.json)
- [smoke summary](../runs/operators/nullclaw_smoke_20260423T140224Z/smoke_summary.json)

## `Pi` Snapshot

`Pi` is now part of the local corpus as a native npm-installed CLI agent. Its
current operative benchmark run is
[attempt-2](../runs/pi__simple_content_warning__attempt-2/result.json).
`attempt-1` proved the adapter and runtime path, but it was polluted by a
runner-side browser-seed hang before classification completed cleanly.

`attempt-2` passed environment boot, the serializer contract check, and the
broader regression context check. It also produced real edits across the model,
serializers, form, migration, frontend, and a benchmark-targeted test file. It
still failed acceptance because the generated tests were not benchmark-safe for
this codebase, static UI wiring did not include the required `admin.py`
surface, and browser seeding had to be cut off by the new timeout guard.

Relevant local artifacts:

- [result.json](../runs/pi__simple_content_warning__attempt-2/result.json)
- [changes.patch](../runs/pi__simple_content_warning__attempt-2/changes.patch)
- [stdout.log](../runs/pi__simple_content_warning__attempt-2/stdout.log)
- [targeted_tests.json](../runs/pi__simple_content_warning__attempt-2/checks/targeted_tests.json)
- [contract_shell.json](../runs/pi__simple_content_warning__attempt-2/checks/contract_shell.json)
- [ui_wiring_static.json](../runs/pi__simple_content_warning__attempt-2/checks/ui_wiring_static.json)
- [regression_context.json](../runs/pi__simple_content_warning__attempt-2/checks/regression_context.json)
- [smoke summary](../runs/operators/pi_smoke_20260428T204821Z/smoke_summary.json)

## Related Documents

- Benchmark plan: [2026-04-21 MediaCMS Benchmark Plan](superpowers/specs/2026-04-21-mediacms-benchmark-plan.md)
- Internal expanded report: [simple_content_warning_forensic_report.internal.md](../runs/reports/simple_content_warning_forensic_report.internal.md)
- Cohort methodology and licensing context: [THIRD_PARTY.md](../THIRD_PARTY.md)
