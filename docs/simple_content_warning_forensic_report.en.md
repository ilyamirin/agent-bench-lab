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

- `yulya-zig` is the current top result and the only agent that now passes the
  full public benchmark path end-to-end in the maintained harness.
- `Qwen Code` remains the strongest external baseline and the first full
  end-to-end success in the project history.
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
meaningful benchmark run passed environment boot and produced real edits across
the model, serializers, form, and a migration, but it still failed the
benchmark because no targeted `content_warning` test file was created, the
contract check failed, UI wiring stayed incomplete, and the run did not
terminate cleanly.

The full artifacts remain local-only and are intentionally omitted from this
public-safe summary.

## `Pi` Snapshot

`Pi` is now part of the local corpus as a native npm-installed CLI agent. Its
current operative benchmark run is the second attempt. The first attempt proved
the adapter and runtime path, but it was polluted by a runner-side
browser-seed hang before classification completed cleanly.

`attempt-2` passed environment boot, the serializer contract check, and the
broader regression context check. It also produced real edits across the model,
serializers, form, migration, frontend, and a benchmark-targeted test file. It
still failed acceptance because the generated tests were not benchmark-safe for
this codebase, static UI wiring did not include the required `admin.py`
surface, and browser seeding had to be cut off by the new timeout guard.

The underlying run logs and smoke artifacts are local-only and are not linked
from the public repository.

## `yulya-zig` Snapshot

`yulya-zig` is the in-repo headless benchmark agent implemented in Zig. It is
currently the top result on `simple_content_warning`.

The decisive difference was not raw code generation quality, but closure
discipline. `yulya-zig` now completes the full benchmark loop: required code
changes, targeted acceptance checks, static UI coverage, seeded browser flow,
and browser-level persistence verification.

This also helped harden the benchmark itself. Along the way, the harness was
tightened around Docker preflight, browser seeding, and ref-based Playwright
verification.

## Related Documents

- Benchmark plan: [2026-04-21 MediaCMS Benchmark Plan](superpowers/specs/2026-04-21-mediacms-benchmark-plan.md)
- Cohort methodology and licensing context: [THIRD_PARTY.md](../THIRD_PARTY.md)
