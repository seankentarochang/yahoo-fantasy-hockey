from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from basketball import adp_mocks as mock
from basketball.cli import parser


class AdpMocksTests(unittest.TestCase):
    def fixture(self):
        cfg = {"teams": 2, "slots": {"PG": 1, "C": 1, "BE": 1}, "position_limits": {"C": 2}}
        players = {i: {"id": i, "name": str(i), "adp": i + .1, "draft_rank": 13 - i,
                       "primary": "PG" if i % 2 else "C", "eligible": ["PG" if i % 2 else "C", "UTIL", "BE"]}
                   for i in range(1, 13)}
        return {"model": SimpleNamespace(cfg=cfg, by_id=players), "pool": list(players),
                "quality": list(players), "market": list(players), "rounds": dict.fromkeys(players, 1),
                "bans": {1}, "published": {"test": {i: i for i in players}}}

    def injury_cfg(self):
        return {"draft": {"injury_policy": {"early_days": 14, "early_rounds": 4, "middle_days": 42,
                                              "late_round": 9, "season_end": "2027-04-11"}}}

    def test_adp_validation_and_explicit_rank_fallback(self):
        for value in (None, 0, -1, 999, True, float("nan"), float("inf"), "2.5"):
            self.assertEqual(mock.market_value({"adp": value, "draft_rank": 17}), 17)
        self.assertEqual(mock.market_value({"adp": 2.5, "draft_rank": 17}), 2.5)

    def test_adp_opponents_use_numerical_adp_not_rank(self):
        data = self.fixture()
        self.assertEqual(mock.opponents(data, "adp", 0)[1], list(range(1, 13)))
        self.assertEqual(mock.opponents(data, "adp", 0), mock.opponents(data, "adp", 99))

    def test_saturated_adp_tail_uses_explicit_espn_fallback(self):
        self.assertEqual(mock.market_value({"adp": 129.9, "draft_rank": 185}), 129.9)
        for value in (130, 139.95, 140.00, 141.20):
            self.assertEqual(mock.market_value({"adp": value, "draft_rank": 185}), 185)

    def test_preference_noise_is_smaller_for_early_picks(self):
        self.assertEqual(mock.preference_sigma(4, 16), 1)
        self.assertEqual(mock.preference_sigma(100, 8), 8)

    def test_seeded_noisy_opponents_are_reproducible(self):
        data = self.fixture()
        self.assertEqual(mock.opponents(data, "loose", 42), mock.opponents(data, "loose", 42))
        self.assertNotEqual(mock.opponents(data, "loose", 42), mock.opponents(data, "loose", 43))

    def test_bans_only_apply_to_our_team_and_rosters_are_complete(self):
        case = mock.simulate(self.fixture(), 2, "adp", 0)
        self.assertEqual(case["picks"][0], {"pick": 1, "team": 1, "id": 1})
        self.assertNotIn(1, case["roster"])
        self.assertEqual(len(case["picks"]), 6)
        self.assertEqual(len({p["id"] for p in case["picks"]}), 6)
        self.assertEqual([p["pick"] for p in case["trace"]], [2, 3, 6])

    def test_timing_window_uses_remaining_adp_and_consecutive_turn_is_greedy(self):
        data = self.fixture()
        data["quality"] = [12, 11] + list(range(1, 11))
        data["bans"] = set()
        case = mock.simulate(data, 1, "adp", 0)
        self.assertEqual(case["trace"][0]["id"], 1)
        self.assertEqual(case["trace"][0]["demand_window"], [1, 2])
        self.assertEqual(case["trace"][1]["id"], 12)
        self.assertEqual(case["trace"][-1]["id"], 11)

    def test_injury_round_boundaries_recomputed_from_draft_date(self):
        at = datetime(2026, 10, 18, 11, tzinfo=timezone.utc)
        for day, earliest in (("2026-11-01", 1), ("2026-11-02", 5), ("2026-11-29", 5),
                              ("2026-11-30", 9), ("2027-04-11", 9), ("2027-04-12", None), ("2026-10-17", None)):
            injury = {"injuries": [{"return_date": day}]}
            self.assertEqual(mock.first_round(self.injury_cfg(), {"status": "OUT"}, injury, at), earliest)

    def test_unknown_season_out_and_suspension_stay_excluded(self):
        cfg, at = self.injury_cfg(), datetime(2026, 10, 18, tzinfo=timezone.utc)
        self.assertIsNone(mock.first_round(cfg, {"status": "OUT"}, None, at))
        self.assertIsNone(mock.first_round(cfg, {"status": "ACTIVE"}, {"out_for_season": True}, at))
        self.assertIsNone(mock.first_round(cfg, {"status": "SUSPENSION"}, None, at))
        self.assertIsNone(mock.first_round(cfg, {"status": "ACTIVE"}, {"injuries": [{"designation": "OUT"}]}, at))

    def test_summary_represents_a_real_case_and_identifies_repeated_adp_logs(self):
        data = self.fixture()
        cases = [mock.simulate(data, 2, f, s) for f in mock.FIELDS for s in range(2)]
        summary = mock.summarize(data, cases)
        self.assertEqual(summary[0]["unique_draft_logs"], 1)
        for row in summary:
            actual = next(c for c in cases if c["field"] == row["field"] and c["seed"] == row["representative_seed"])
            self.assertEqual([p["id"] for p in row["representative"]], actual["roster"])
            for rnd in row["rounds"]:
                self.assertEqual(sum(c["count"] for c in rnd["choices"]), 2)

    def test_invalid_run_does_not_read_or_mutate_inputs(self):
        with patch.object(mock, "prepare") as prepare:
            for slot, count in ((0, 1), (3, 1), (1, 0), (1, 1001)):
                with self.assertRaises(ValueError):
                    mock.run({"teams": 2}, slot, count)
            prepare.assert_not_called()

    def test_cli_refresh_is_explicit_and_has_no_execution_flag(self):
        args = parser().parse_args(["research", "adp-mocks", "--slot", "15", "--count", "100", "--refresh-market"])
        self.assertTrue(args.refresh_market)
        self.assertFalse(hasattr(args, "execute"))

    def test_default_cli_tests_all_positions(self):
        args = parser().parse_args(["research", "adp-mocks"])
        self.assertIsNone(args.slot)
        self.assertEqual(args.count, 25)

    def test_summary_does_not_mix_different_pick_positions(self):
        data = self.fixture()
        cases = [mock.simulate(data, slot, f, 0) for f in mock.FIELDS for slot in (1, 2)]
        summary = mock.summarize(data, cases)
        self.assertEqual(len(summary), 6)
        for row in summary:
            self.assertEqual(row["rounds"][0]["pick"], row["slot"])
            self.assertEqual(row["drafts"], 1)


if __name__ == "__main__":
    unittest.main()
