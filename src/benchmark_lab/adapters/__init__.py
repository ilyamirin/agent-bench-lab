"""Agent adapters for the benchmark lab."""

from .aider import AiderAdapter
from .cline import ClineAdapter
from .hermes import HermesAdapter
from .kilocode import KiloCodeAdapter
from .missing import MissingBinaryAdapter
from .nullclaw import NullClawAdapter
from .opencode import OpenCodeAdapter
from .openclaw import OpenClawAdapter
from .openhands import OpenHandsAdapter
from .pi import PiAdapter
from .qwen_code import QwenCodeAdapter
from ..models import CompatibilityStatus


def build_adapter_registry() -> dict[str, object]:
    return {
        "qwen-code": QwenCodeAdapter(),
        "aider": AiderAdapter(),
        "cline": ClineAdapter(),
        "opencode": OpenCodeAdapter(),
        "kilocode": KiloCodeAdapter(),
        "nullclaw": NullClawAdapter(),
        "pi": PiAdapter(),
        "openhands": OpenHandsAdapter(),
        "hermes-agent": HermesAdapter(),
        "openclaw": OpenClawAdapter(),
        "codebuff": MissingBinaryAdapter(
            "codebuff",
            ["codebuff"],
            missing_status=CompatibilityStatus.INCOMPATIBLE_TRANSPORT,
            missing_reason="official docs do not currently prove a native headless OpenRouter CLI run path for strict benchmark execution",
            implemented_status=CompatibilityStatus.INCOMPATIBLE_TRANSPORT,
            implemented_reason="CLI is present, but native strict OpenRouter headless execution is still not proven",
            extra_details={"doc_decision": "transport_not_proven"},
        ),
        "crush": MissingBinaryAdapter(
            "crush",
            ["crush"],
            missing_status=CompatibilityStatus.INCOMPATIBLE_TRANSPORT,
            missing_reason="official docs confirm OpenRouter provider support, but non-interactive batch execution is still not documented as a stable CLI mode",
            implemented_status=CompatibilityStatus.INCOMPATIBLE_TRANSPORT,
            implemented_reason="CLI is present, but native non-interactive batch execution is not yet documented as stable",
            extra_details={"doc_decision": "headless_mode_not_proven"},
        ),
    }


__all__ = [
    "AiderAdapter",
    "ClineAdapter",
    "HermesAdapter",
    "KiloCodeAdapter",
    "NullClawAdapter",
    "OpenCodeAdapter",
    "OpenClawAdapter",
    "OpenHandsAdapter",
    "PiAdapter",
    "QwenCodeAdapter",
    "MissingBinaryAdapter",
    "build_adapter_registry",
]
