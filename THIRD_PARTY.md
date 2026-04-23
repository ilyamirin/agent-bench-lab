# Third-Party Components

This repository contains benchmark harness code under the MIT license in the
repository root `LICENSE` file.

External projects used by this repository are documented below. This file is
compliance-oriented repository metadata, not legal advice.

## Shipped / Referenced Through This Repository

### MediaCMS

- Upstream repository: <https://github.com/mediacms-io/mediacms.git>
- How this repository uses it: tracked as the `upstream/mediacms` git submodule and used as the benchmark target application
- Distribution status: referenced and checked out through the submodule; not vendored into the benchmark harness code
- Upstream license: `AGPL-3.0` (`upstream/mediacms/LICENSE.txt`)
- Compliance note: local edits inside the submodule are not intended to be part of public commits from this repository

## Local-Only Optional Benchmark Targets

These repos are cloned locally into `.agents/` for evaluation workflows. They
are not redistributed as part of this repository.

### Aider

- Upstream repository: <https://github.com/Aider-AI/aider>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `Apache-2.0` (`.agents/aider/LICENSE.txt`)

### Cline

- Upstream repository: <https://github.com/cline/cline>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `Apache-2.0` (`.agents/cline/LICENSE`)

### Codebuff

- Upstream repository: <https://github.com/CodebuffAI/codebuff>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `Apache-2.0` (`.agents/codebuff/LICENSE`)
- Compliance note: upstream also provides a `NOTICE` file (`.agents/codebuff/NOTICE`)

### Crush

- Upstream repository: <https://github.com/charmbracelet/crush>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `FSL-1.1-MIT Future License` (`.agents/crush/LICENSE.md`)
- Compliance note: this is not a plain MIT/Apache license and should be reviewed directly before any redistribution of Crush code

### Hermes Agent

- Upstream repository: <https://github.com/NousResearch/hermes-agent>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `MIT` (`.agents/hermes-agent/LICENSE`)

### Kilo Code

- Upstream repository: <https://github.com/kilo-org/kilocode>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `MIT` (`.agents/kilocode/LICENSE`)

### OpenClaw

- Upstream repository: <https://github.com/openclaw/openclaw>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `MIT` (`.agents/openclaw/LICENSE`)

### OpenCode

- Upstream repository: <https://github.com/anomalyco/opencode>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: `MIT` (`.agents/opencode/LICENSE`)

### OpenHands

- Upstream repository: <https://github.com/OpenHands/OpenHands>
- How this repository uses it: optional local benchmark target
- Distribution status: local-only clone, not shipped
- Upstream license: mixed; MIT for most of the repository with separate licensing noted for `enterprise/` content (`.agents/openhands/LICENSE`)
- Compliance note: review upstream licensing boundaries directly before redistributing any OpenHands code

### Qwen Code

- Upstream repository: <https://github.com/QwenLM/qwen-code>
- How this repository uses it: optional local benchmark target and benchmark control agent
- Distribution status: local-only clone, not shipped
- Upstream license: `Apache-2.0` (`.agents/qwen-code/LICENSE`)
