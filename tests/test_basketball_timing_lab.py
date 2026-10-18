import copy
from types import SimpleNamespace
import unittest

from basketball import timing_lab as lab
from basketball.cli import parser
from basketball.config import active_slots, roster_size
from basketball.planner import assign, legal_roster


class TimingLabTests(unittest.TestCase):
    def fixture(self):
        cfg = {"teams": 2, "slots": {"PG": 1, "C": 1, "BE": 1}, "position_limits": {"C": 2}}
        players = {i: {"id": i, "name": str(i), "draft_rank": i, "adp": 13-i,
                       "primary": "PG" if i % 2 else "C", "eligible": ["PG" if i % 2 else "C", "BE"],
                       "fpg": 20-i, "ros": (20-i)*70, "ranked": True} for i in range(1, 13)}
        def legal(roster, pid):
            ps = [players[p] for p in (*roster, pid)]
            return legal_roster(ps, cfg) and len(active_slots(cfg))-len(assign(ps, active_slots(cfg))) <= roster_size(cfg)-len(ps)
        return {"model": SimpleNamespace(cfg=cfg, by_id=players), "quality": list(players), "quality_rank": {i: i for i in players},
                "pool": list(players), "espn_market": list(players), "rw_ranks": {i: i for i in players},
                "rounds": dict.fromkeys(players, 1), "bans": set(), "legal": legal}

    def test_current_window_includes_our_pick_and_buffers_add_market_players(self):
        data = self.fixture()
        data["quality"] = [8, 4]+[i for i in data["quality"] if i not in (8, 4)]
        for policy, expected, window in (("current", 1, 3), ("buffer4", 4, 7), ("buffer8", 8, 11), ("greedy", 8, None)):
            pid, trace = lab.choose(data, [], set(), 1, 2, policy)
            self.assertEqual(pid, expected)
            self.assertEqual(trace["window"], window)

    def test_banned_and_round_ineligible_players_remain_in_demand_window(self):
        data = self.fixture()
        data["bans"] = {1}
        data["rounds"][2] = 3
        data["quality"] = [5, 3, 4, 1, 2]+list(range(6, 13))
        pid, trace = lab.choose(data, [], set(), 1, 2, "current")
        self.assertEqual(pid, 3)
        self.assertEqual(trace["market_position"], 3)

    def test_consecutive_and_final_picks_do_not_defer_for_timing(self):
        data = self.fixture()
        data["quality"] = [8]+[i for i in data["quality"] if i != 8]
        for gap in (0, None):
            pid, trace = lab.choose(data, [], set(), 1, gap, "buffer8")
            self.assertEqual(pid, 8)
            self.assertIsNone(trace["window"])

    def test_multi_position_player_cannot_cover_two_core_slots(self):
        weights = (1, .8, .4, .3, .2)
        guard = {"eligible": ["PG", "SG"]}
        self.assertEqual(lab.weighted_coverage([guard], weights), 1)
        self.assertEqual(lab.weighted_coverage([guard, {"eligible": ["PG"]}], weights), 1.8)

    def test_scarcity_fills_a_core_hole_within_three_published_spots(self):
        data = self.fixture()
        pid, trace = lab.choose(data, [3], {3}, 2, 5, "scarcity3")
        self.assertEqual(pid, 2)
        self.assertTrue(trace["scarcity_changed"])
        self.assertGreater(trace["scarcity_gain"], 0)
        self.assertEqual(data["rw_ranks"][pid]-data["rw_ranks"][trace["best_in_tier"]], 1)

    def test_scarcity_cannot_jump_four_published_spots_or_use_unpublished_tail(self):
        data = self.fixture()
        data["rw_ranks"] = {1: 10, 2: 14}
        self.assertEqual(lab.choose(data, [3], {3}, 2, 5, "scarcity3")[0], 1)
        data["rw_ranks"] = {}
        self.assertEqual(lab.choose(data, [3], {3}, 2, 5, "scarcity3")[0], 1)

    def test_final_selection_ignores_scarcity(self):
        data = self.fixture()
        self.assertEqual(lab.choose(data, [3], {3}, 2, None, "scarcity3")[0], 1)

    def test_scarcity_does_not_change_when_only_projection_values_change(self):
        data = self.fixture()
        before = lab.choose(data, [3], {3}, 2, 5, "scarcity3")[0]
        for p in data["model"].by_id.values():
            p.update(fpg=-p["fpg"]*100, ros=0)
        self.assertEqual(lab.choose(data, [3], {3}, 2, 5, "scarcity3")[0], before)

    def test_all_variants_finish_unique_legal_rosters_with_identical_input_queues(self):
        data = self.fixture()
        queues = lab.opponent_queues(data, "typical", 3)
        original = copy.deepcopy(queues)
        for policy in lab.POLICIES:
            case = lab.simulate(data, 1, "typical", 3, policy, queues)
            self.assertEqual(len(case["picks"]), 6)
            self.assertEqual(len({p["id"] for p in case["picks"]}), 6)
            self.assertEqual(len(case["roster"]), 3)
        self.assertEqual(queues, original)

    def test_bans_apply_only_to_our_team(self):
        data = self.fixture()
        data["bans"] = {1}
        case = lab.simulate(data, 2, "espn", 0, "current")
        self.assertEqual(case["picks"][0]["id"], 1)
        self.assertNotIn(1, case["roster"])

    def test_espn_control_follows_rank_not_adp(self):
        data = self.fixture()
        self.assertEqual(lab.opponent_queues(data, "espn", 0)[1], list(range(1, 13)))

    def test_paired_summary_compares_only_matching_field_slot_seed(self):
        data = self.fixture()
        rows = []
        for policy in ("current", "buffer4"):
            case = lab.simulate(data, 1, "typical", 3, policy)
            rows.append({"field": "typical", "slot": 1, "seed": 3, "policy": policy, **lab.evaluate(data, case)})
        rows[1].update(rank_score=rows[0]["rank_score"]-10,
                       projected_season_points=rows[0]["projected_season_points"]*1.1,
                       starter_fpg_sum=rows[0]["starter_fpg_sum"]*1.1)
        summary, by_slot = lab.summaries(rows)
        improved = next(r for r in summary if r["field"] == "typical" and r["policy"] == "buffer4")
        self.assertEqual(improved["mean_rank_gain_vs_current"], 10)
        self.assertAlmostEqual(improved["projected_season_gain_pct_vs_current"], 10)
        self.assertEqual(len(by_slot), 2)

    def test_deferred_loss_excludes_targets_available_at_next_pick(self):
        data = self.fixture()
        case = lab.simulate(data, 1, "espn", 0, "greedy")
        case["trace"] = [{"pick": 1, "id": 1, "best_available": 2, "next_pick": 4,
                          "buffered_reach": False, "scarcity_changed": False, "late_coverage_pressure": False}]
        case["picks"] = [{"pick": 4, "id": 2}]
        self.assertEqual(lab.evaluate(data, case)["deferred_lost"], 0)
        case["picks"][0]["pick"] = 3
        self.assertEqual(lab.evaluate(data, case)["deferred_lost"], 1)

    def test_research_cli_has_no_execute_flag(self):
        args = parser().parse_args(["research", "timing-mocks"])
        self.assertFalse(hasattr(args, "execute"))


if __name__ == "__main__":
    unittest.main()
