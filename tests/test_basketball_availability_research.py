"""Availability cohorts, opportunity normalization and information boundaries."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from basketball import availability_research as availability
from basketball.empirical import Store
from basketball.config import write_json
from basketball.backtest import digest


def player(games, opportunities=82):
    return {"games": games, "minutes": games*30, "game_share": games/opportunities,
            "name": "A Player", "stats": {}}


class AvailabilityTests(unittest.TestCase):
    def test_shortened_season_is_normalized_without_floor(self):
        store = Store({2020: {"a": player(60, 72)}, 2021: {"a": player(36, 72)}})
        self.assertAlmostEqual(availability.no_floor_games(store, "a", 2022), 82*(.8*.5+.2*60/72))
        store = Store({2021: {"a": player(20)}})
        self.assertAlmostEqual(availability.no_floor_games(store, "a", 2022), 20)

    def test_absence_is_zero_after_debut_but_predebut_is_not_absence(self):
        store = Store({2024: {"a": player(70)}, 2025: {}})
        self.assertAlmostEqual(availability.no_floor_games(store, "a", 2026), 14)
        self.assertAlmostEqual(availability.no_floor_games(store, "a", 2025), 70)
        self.assertEqual(availability.features(store, "a", 2026)[0:4], [0, 0, 0, 1])
        self.assertEqual(availability.features(store, "a", 2025)[4:8], [0, 0, 0, 0])

    def test_candidates_and_fit_include_retired_or_absent_target_players(self):
        store = Store({2022: {"a": player(60), "b": player(19)}, 2023: {}, 2024: {}})
        self.assertEqual(availability.candidates(store, 2023), ["a"])
        model = availability.fit(store, [2023], 1)
        self.assertEqual(model["training_samples"], 1)
        self.assertEqual(model["zero_target_samples"], 1)
        self.assertAlmostEqual(availability.predict(model, availability.features(store, "a", 2023)), 0)

    def test_features_and_prior_fit_cannot_see_future_outcomes(self):
        seasons = {2020: {"a": player(50)}, 2021: {"a": player(65)},
                   2022: {"a": player(55)}, 2023: {"a": player(45)}}
        store = Store(seasons)
        model = availability.fit(store, [2021, 2022], 10)
        values = availability.features(store, "a", 2023)
        changed = deepcopy(seasons)
        changed[2023] = {}; changed[2024] = {"a": player(82)}
        self.assertEqual(availability.features(Store(changed), "a", 2023), values)
        self.assertEqual(availability.fit(Store(changed), [2021, 2022], 10), model)

    def test_predictions_are_bounded(self):
        model = {"mean": [0], "scale": [1], "coefficients": [0, 10]}
        self.assertEqual(availability.predict(model, [1]), 82)
        self.assertEqual(availability.predict(model, [-1]), 0)

    def test_dated_forecast_missing_is_unknown_not_zero(self):
        self.assertIsNone(availability.forecast_games({}))
        self.assertAlmostEqual(availability.forecast_games({"FP": 4321.4, "FP/G": 58.4}), 74, places=1)
        self.assertEqual(availability.forecast_games({"G": 0}), 0)
        for forecast in ({"G": -1}, {"G": float("nan")}, {"G": 90}):
            with self.assertRaises(ValueError): availability.forecast_games(forecast)

    def test_forward_forecasts_replace_history_and_do_not_double_count_sources(self):
        p = {"splits": [{"season": 2027, "source": 1, "stats": {"GP": 60}},
                        {"season": 2026, "source": 0, "stats": {"GP": 82}}]}
        sources = availability.forward_games(p, {"games": 70}, {"games": 65}, 2027)
        self.assertEqual(sources, {"ESPN": 60, "Hashtag": 70, "FantasyPros": 65})
        self.assertEqual(availability.with_games({"fpg": 40}, sum(sources.values())/3)["season_points"], 2600)
        p["splits"].append(p["splits"][0])
        with self.assertRaisesRegex(ValueError, "Ambiguous"): availability.forward_games(p, season=2027)

    def test_forward_zero_is_valid_and_invalid_values_fail_closed(self):
        self.assertEqual(availability.forward_games({}, {"games": 0}), {"Hashtag": 0})
        for value in (float("inf"), -1, 83, True):
            with self.assertRaises(ValueError): availability.forward_games({}, {"games": value})

    def test_commands_remain_comparison_only(self):
        from basketball.cli import parser
        for action in ("availability-backtest", "availability-rank"):
            args = parser().parse_args(["research", action])
            self.assertFalse(hasattr(args, "execute"))

    def test_uncovered_players_keep_market_slots_in_source_comparison(self):
        data = {"market": [1, 2, 3, 4]}
        rows = [{"id": 2, "primary": "PG", "season_points": 100},
                {"id": 4, "primary": "PG", "season_points": 200}]
        order, _ = availability.order_for(data, rows, {"teams": 1, "slots": {"PG": 1}})
        self.assertEqual(order, [1, 4, 3, 2])

    def test_saved_model_rejects_changed_data_code_or_season(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"research-availability"
            cfg = {"_data": folder, "season": 2027}
            signature = {"data_sha256": "data", "code_sha256": {"a": "old"}}
            selection = {**signature, "selected_alpha": 10}
            model = {**signature, "target_season": 2027, "selection_sha256": digest(selection)}
            for name, value in (("selection", selection), ("model", model)):
                write_json(root/(name+".json"), value)
                write_json(root/(name+"-lock.json"), {"sha256": digest(value)})
            with patch.object(availability, "fingerprint", return_value=signature):
                self.assertEqual(availability.locked_model(cfg, {}), model)
                with self.assertRaises(ValueError): availability.locked_model({**cfg, "season": 2028}, {})
            for changed in ({**signature, "data_sha256": "different"},
                            {**signature, "code_sha256": {"a": "new"}}):
                with patch.object(availability, "fingerprint", return_value=changed):
                    with self.assertRaises(ValueError): availability.locked_model(cfg, {})

    def test_current_board_uses_forward_games_once_then_caps_and_preserves_ban(self):
        from basketball import research_board
        with tempfile.TemporaryDirectory() as folder:
            cfg = {"_data": folder, "season": 2027, "scoring": {}, "teams": 1, "slots": {"PG": 1}}
            row = {"id": 1, "name": "A Player", "team": "X", "eligible": ["PG"], "injury": None,
                   "ban": "Personal ban", "espn_rank": 1, "rotowire_rank": 1, "flags": [],
                   "injury_opportunity_cap": 50}
            inputs = {"snapshot": {"players": [{"id": 1, "primary": "PG", "splits": [
                {"season": 2027, "source": 1, "stats": {"GP": 60}}]}]},
                "public_projections": [], "fantasypros_opportunities": []}
            base = {"rows": [row], "as_of": "2026-10-17T12:00:00+00:00", "inputs_sha256": "inputs"}
            store = Store({2026: {"a": player(50)}})
            production = {"per_game": {}, "fpg": 40, "games": 40, "season_points": 1600}
            with patch.object(research_board, "build"), \
                 patch.object(research_board, "match_outside", return_value=({}, [])), \
                 patch.object(availability.empirical, "load_seasons", return_value=(store, {})), \
                 patch.object(availability, "locked_model", return_value={}), \
                 patch.object(availability, "predict", return_value=10), \
                 patch.object(availability.value_board, "projection", return_value=production), \
                 patch.object(availability, "read_json", side_effect=[base, inputs]):
                availability.current(cfg)
            from basketball.config import read_json
            result = read_json(Path(folder)/"research-availability/rankings.json")["rows"][0]
            self.assertEqual(result["games"], 50)  # min(60, 50), no historic blend or second subtraction.
            self.assertEqual(result["season_points"], 2000)
            self.assertEqual(result["ban"], "Personal ban")
            self.assertIsNone(result["personal_rank"])


if __name__ == "__main__": unittest.main()
