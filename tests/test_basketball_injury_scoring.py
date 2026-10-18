"""Scoring algebra, component isolation and chronological evaluation boundaries."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from basketball import empirical, injury_history, injury_scoring as scoring
from basketball.backtest import digest
from basketball.config import write_json

WEIGHTS = {"FGM": 2, "FGA": -1, "FTM": 1, "FTA": -1, "3PM": 1, "REB": 1,
           "AST": 2, "STL": 3, "BLK": 3, "TO": -2, "PTS": 1}


def player(games=70):
    pg = {"PTS": 20, "FGM": 7, "FGA": 15, "FTM": 4, "FTA": 5, "3PM": 2,
          "REB": 5, "AST": 4, "STL": 1, "BLK": 1, "TO": 2, "3PA": 5}
    return {"name": "Player One", "games": games, "game_share": games/82, "minutes": games*30,
            "stats": {k: v*games for k, v in pg.items()}}


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.store = empirical.Store({y: {"p": player()} for y in range(2017, 2024)})
        self.production = scoring.Production(self.store, injury_history.History([]), WEIGHTS)
        self.rates = {k: v/30 for k, v in player()["stats"].items() if k in empirical.FIELDS}
        self.rates = {k: v/70 for k, v in self.rates.items()}

    def test_scoring_line_uses_exact_league_weights_without_flat_injury_discount(self):
        line = scoring.score_line(self.rates, 30, 60, WEIGHTS)
        self.assertAlmostEqual(line["fpg"], 35)
        self.assertAlmostEqual(line["season_points"], 2100)
        self.assertAlmostEqual(line["per_game"]["PTS"],
                               2*line["per_game"]["FGM"]+line["per_game"]["3PM"]+line["per_game"]["FTM"])
        self.assertEqual(scoring.score_line(self.rates, 30, 0, WEIGHTS)["season_points"], 0)
        self.assertLess(scoring.score_line(self.rates, 30, 60, {"TO": -2})["season_points"], 0)

    def test_invalid_workload_or_unsupported_scoring_fails(self):
        for minutes, games in ((49, 60), (30, 83), (-1, 60), (30, float("nan"))):
            with self.assertRaises(ValueError): scoring.score_line(self.rates, minutes, games, WEIGHTS)
        with self.assertRaises(ValueError): scoring.score_line(self.rates, 30, 60, {"UNSUPPORTED": 1})

    def test_injury_features_extend_the_same_production_representation(self):
        base = self.production.features("p", 2022, False)
        injury = self.production.features("p", 2022, True)
        self.assertEqual(len(base), 42)
        self.assertEqual(injury[:42], base)
        self.assertEqual(len(injury), 42+len(injury_history.FEATURE_NAMES))

    def test_rate_and_minutes_training_cohorts_are_identical(self):
        for injury in (False, True):
            rates = self.production.fit((2020, 2021), 10, injury, "rates")
            minutes = self.production.fit((2020, 2021), 10, injury, "minutes")
            self.assertEqual(rates["training_samples"], minutes["training_samples"])
            self.assertEqual(rates["mean"], minutes["mean"])
            rate = self.production.predict(rates, "p", 2022)
            minute = self.production.predict(minutes, "p", 2022)
            self.assertAlmostEqual(empirical.points(rate, WEIGHTS)*minute, 35)

    def test_no_target_actuals_enter_scoring_features_or_prior_fits(self):
        changed = deepcopy(self.store.seasons); changed[2022] = {}; changed[2023] = {"p": player(1)}
        other = scoring.Production(empirical.Store(changed), injury_history.History([]), WEIGHTS)
        for injury in (False, True):
            self.assertEqual(self.production.features("p", 2022, injury), other.features("p", 2022, injury))
            self.assertEqual(self.production.fit((2020, 2021), 10, injury, "rates"),
                             other.fit((2020, 2021), 10, injury, "rates"))

    def test_training_that_overlaps_forecast_is_rejected(self):
        model = self.production.fit((2020, 2021), 10, False, "minutes")
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.production.predict(model, "p", 2021)

    def test_season_errors_keep_zero_game_players_conditional_errors_do_not(self):
        self.store.seasons[2022] = {"q": player(20)}
        prediction = scoring.score_line(self.rates, 30, 60, WEIGHTS)
        errors = scoring.collect_errors(self.production, {"model": {"p": prediction, "q": prediction}}, 2022)
        result = scoring.summarize(errors)["model"]
        self.assertEqual(result["counts"]["candidates"], 2)
        self.assertEqual(result["counts"]["zero_games"], 1)
        self.assertEqual(result["metrics"]["season_points"]["players"], 2)
        self.assertEqual(result["metrics"]["per_game"]["players"], 1)
        self.assertEqual(result["metrics"]["per_game_20plus"]["players"], 1)
        self.assertAlmostEqual(result["metrics"]["zero_game_projected_points"]["mae"], 2100)

    def test_component_combinations_isolate_production_and_availability(self):
        prior = {"forecasts": {"2022": {"base_games": {"p": {"games": 70}}, "injury_games": {"p": {"games": 50}}}}}
        selected = {k: 1 for k in ("base_rates", "base_minutes", "injury_rates", "injury_minutes")}
        def fit(years, alpha, injury, target):
            return {"injury": injury, "target": target}
        def predict(model, pid, year):
            return self.rates if model["target"] == "rates" else 24 if model["injury"] else 30
        with patch.object(self.production, "fit", side_effect=fit), patch.object(self.production, "predict", side_effect=predict):
            _, result = scoring.forecast(self.production, 2022, selected, prior)
        base, availability, production, full = (result[n]["p"] for n in scoring.POLICIES)
        self.assertEqual(base["fpg"], availability["fpg"])
        self.assertEqual(base["games"], production["games"])
        self.assertEqual(production["fpg"], full["fpg"])
        self.assertEqual(availability["games"], full["games"])
        self.assertAlmostEqual(full["season_points"], 35*.8*50)

    def test_locked_games_reject_changed_configuration_or_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"research-injury"
            cfg = {"_data": folder, "scoring": WEIGHTS, "teams": 16, "slots": {}, "position_limits": {}}
            fingerprints = {"data_sha256": "data", "code_sha256": {"a": "hash"}}
            selection = {**fingerprints, "scoring": WEIGHTS}
            evidence = {**fingerprints, "selection_sha256": digest(selection),
                        "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring")}}
            for name, value in (("selection", selection), ("decisions", evidence)):
                write_json(root/(name+".json"), value)
                write_json(root/(name+"-lock.json"), {"sha256": digest(value)})
            with patch.object(scoring.injury_research, "fingerprints", return_value=fingerprints):
                self.assertEqual(scoring.locked_games(cfg, {}, {}), evidence)
                with self.assertRaisesRegex(ValueError, "configuration"):
                    scoring.locked_games({**cfg, "teams": 12}, {}, {})
                write_json(root/"decisions.json", {**evidence, "changed": True})
                with self.assertRaisesRegex(ValueError, "lock"):
                    scoring.locked_games(cfg, {}, {})

    def test_pooled_errors_preserve_counts_and_use_paired_observations(self):
        one = {"model": {"counts": {"candidates": 1}, "errors": {"season_points": [10]}}}
        two = {"model": {"counts": {"candidates": 2}, "errors": {"season_points": [-20, 30]}}}
        result = scoring.pooled({"2023": one, "2024": two})["model"]
        self.assertEqual(result["counts"]["candidates"], 3)
        self.assertEqual(result["metrics"]["season_points"]["mae"], 20)

    def test_later_injury_coverage_and_execute_routing_remain_blocked(self):
        self.store.seasons[2025] = {"p": player()}
        with self.assertRaisesRegex(ValueError, "missing coverage"):
            self.production.research.frame(2026)
        from basketball.cli import parser
        self.assertFalse(hasattr(parser().parse_args(["research", "injury-scoring-backtest"]), "execute"))


if __name__ == "__main__": unittest.main()
