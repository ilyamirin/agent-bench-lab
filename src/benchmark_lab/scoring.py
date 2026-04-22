from __future__ import annotations

from .models import ScoreCard


def score_v1(automated_checks: list[dict], duration_seconds: float | None) -> ScoreCard:
    passed = sum(1 for item in automated_checks if item.get("passed"))
    total = max(1, len(automated_checks))
    if passed == total:
        task_solved = 4
    elif passed >= total - 1:
        task_solved = 3
    elif passed >= total // 2:
        task_solved = 2
    elif passed > 0:
        task_solved = 1
    else:
        task_solved = 0

    if duration_seconds is None:
        speed_cost = None
    elif duration_seconds <= 120:
        speed_cost = 4
    elif duration_seconds <= 300:
        speed_cost = 3
    elif duration_seconds <= 600:
        speed_cost = 2
    else:
        speed_cost = 1

    pending_axes = ["reliability", "quality"]
    if speed_cost is None:
        pending_axes.append("speed/cost")

    return ScoreCard(
        task_solved=task_solved,
        reliability=None,
        quality=None,
        speed_cost=speed_cost,
        pending_axes=pending_axes,
    )

