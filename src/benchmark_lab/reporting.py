from __future__ import annotations

import json
import math
from pathlib import Path

from .models import RunResult, ScoreCard


AXES = [
    ("task solved", "task_solved"),
    ("reliability", "reliability"),
    ("quality", "quality"),
    ("speed/cost", "speed_cost"),
]


def write_run_result_json(run_result: RunResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(run_result.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def render_markdown_summary(results: list[RunResult]) -> str:
    lines = [
        "# Benchmark Pilot Summary",
        "",
        "pending axes are reported per run until full scoring is available.",
        "",
        "| Agent | Task | Status | Pending |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        pending = ", ".join(result.scores.pending_axes) if result.scores.pending_axes else "none"
        lines.append(
            f"| {result.run_spec.agent_id} | {result.run_spec.task_id} | {result.status.value} | {pending} |"
        )
    return "\n".join(lines) + "\n"


def render_radar_chart_svg(title: str, score_card: ScoreCard) -> str:
    width = 440
    height = 440
    center_x = width / 2
    center_y = height / 2
    radius = 140

    def _score_for(attr: str) -> float:
        value = getattr(score_card, attr)
        if value is None:
            return 0.0
        return max(0.0, min(4.0, float(value))) / 4.0

    points: list[str] = []
    labels: list[str] = []
    for index, (label, attr) in enumerate(AXES):
        angle = -math.pi / 2 + (2 * math.pi * index / len(AXES))
        axis_x = center_x + radius * math.cos(angle)
        axis_y = center_y + radius * math.sin(angle)
        score_radius = radius * _score_for(attr)
        point_x = center_x + score_radius * math.cos(angle)
        point_y = center_y + score_radius * math.sin(angle)
        points.append(f"{point_x:.2f},{point_y:.2f}")
        label_x = center_x + (radius + 34) * math.cos(angle)
        label_y = center_y + (radius + 34) * math.sin(angle)
        labels.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" font-size="14" '
            f'text-anchor="middle" fill="#1f2937">{label}</text>'
        )

    polygon = " ".join(points)
    pending = ", ".join(score_card.pending_axes) if score_card.pending_axes else "none"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{center_x}" y="36" font-size="20" text-anchor="middle" fill="#0f172a">{title}</text>
  <text x="{center_x}" y="58" font-size="12" text-anchor="middle" fill="#64748b">pending: {pending}</text>
  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" stroke="#cbd5e1" stroke-width="1" />
  <circle cx="{center_x}" cy="{center_y}" r="{radius * 0.75:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1" />
  <circle cx="{center_x}" cy="{center_y}" r="{radius * 0.5:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1" />
  <circle cx="{center_x}" cy="{center_y}" r="{radius * 0.25:.2f}" fill="none" stroke="#cbd5e1" stroke-width="1" />
  <polygon points="{polygon}" fill="rgba(37, 99, 235, 0.24)" stroke="#2563eb" stroke-width="2" />
  {''.join(labels)}
</svg>
"""
