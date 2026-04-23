from __future__ import annotations

import unittest

from benchmark_lab.scoring import score_v1


class ScoringTest(unittest.TestCase):
    def test_single_failed_check_scores_zero_not_three(self) -> None:
        score = score_v1([{"name": "environment_boot", "passed": False}], 30.0)

        self.assertEqual(score.task_solved, 0)
        self.assertEqual(score.speed_cost, 4)

    def test_empty_checks_score_zero_not_three(self) -> None:
        score = score_v1([], None)

        self.assertEqual(score.task_solved, 0)
        self.assertIsNone(score.speed_cost)
        self.assertEqual(score.pending_axes, ["reliability", "quality", "speed/cost"])


if __name__ == "__main__":
    unittest.main()
