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

## Related Documents

- Benchmark plan: [2026-04-21 MediaCMS Benchmark Plan](superpowers/specs/2026-04-21-mediacms-benchmark-plan.md)
- Internal expanded report: `runs/reports/simple_content_warning_forensic_report.internal.md`
- Cohort methodology and licensing context: [THIRD_PARTY.md](../THIRD_PARTY.md)
