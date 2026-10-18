"""Censored injury histories and fair output/availability comparisons."""
from copy import deepcopy
from datetime import date
from pathlib import Path
import tempfile
import unittest

from basketball import injury_history as history, injury_research as research
from basketball.empirical import Store
from basketball.research_data import FIELDS


def event(day, note, name="Player One", returned=False):
    return {"Date": day, "Team": "A", "Acquired": name if returned else "",
            "Relinquished": "" if returned else name, "Notes": note}


def season_player(games=70, opportunities=82):
    return {"name": "Player One", "games": games, "game_share": games/opportunities,
            "minutes": games*30, "stats": {k: games*(20 if k == "PTS" else 1) for k in FIELDS}}


class InjuryHistoryTests(unittest.TestCase):
    def setUp(self):
        self.store = Store({2017: {"p": season_player()}, 2018: {"p": season_player()},
                            2019: {"p": season_player()}, 2020: {"p": season_player()},
                            2021: {}, 2022: {"p": season_player()}})

    def test_medical_classification_excludes_rest_personal_and_generic_il(self):
        cases = {"placed on IL": None, "personal reasons": None, "rest": "rest", "illness": "illness",
                 "torn ACL in right knee": "knee", "torn left Achillles tendon": "achilles",
                 "sprained left ankle": "ankle", "head coach illness": None, "strained hamstring": "hamstring",
                 "bruised ribs": "other", "abdominal contusion": "other", "chest pain": "other"}
        for text, expected in cases.items():
            self.assertEqual(history.classify(text), expected, text)
        self.assertTrue(history.SEVERE.search("torn left Achillles tendon"))

    def test_aliases_match_only_one_prior_identity(self):
        identities = {"playerone": "p", "othertwo": "q"}
        self.assertEqual(history.resolve("Player One (Alternate)", identities), "p")
        self.assertEqual(history.resolve("Player One / Player One (Alternate)", identities), "p")
        self.assertIsNone(history.resolve("Player One / Other Two", identities))

    def test_future_return_and_injury_do_not_change_preseason_features(self):
        rows = [event("2019-09-01", "torn ACL in left knee")]
        before = history.History(rows).summary(self.store, "p", 2020)
        later = rows+[event("2019-10-02", "activated from IL", returned=True),
                      event("2020-04-01", "sprained left ankle")]
        after = history.History(later).summary(self.store, "p", 2020)
        self.assertEqual(before, after)
        self.assertEqual(before["observed_days"], 30)
        self.assertEqual(before["episodes"], 1)
        self.assertEqual(len(before["features"]), len(history.FEATURE_NAMES))

    def test_repeat_reports_coalesce_but_recorded_return_separates_episodes(self):
        rows = [event("2019-08-01", "knee injury"), event("2019-08-02", "placed on IL with knee injury"),
                event("2019-08-04", "surgery on knee"), event("2019-08-05", "activated from IL", returned=True),
                event("2019-08-06", "knee injury"), event("2019-08-08", "returned to lineup", returned=True)]
        result = history.History(rows).summary(self.store, "p", 2020)
        self.assertEqual(result["episodes"], 2)
        self.assertEqual(result["recurrences"], 1)
        self.assertTrue(result["severe"])
        self.assertEqual(result["observed_days"], 6)

    def test_overlapping_absences_count_calendar_days_once(self):
        rows = [event("2019-08-01", "knee injury"), event("2019-08-02", "ankle injury"),
                event("2019-08-05", "activated from IL", returned=True)]
        result = history.History(rows).summary(self.store, "p", 2020)
        self.assertEqual(result["observed_days"], 4)
        self.assertLessEqual(result["features"][1], 1)

    def test_cutoff_boundary_and_approximate_dates_are_excluded(self):
        rows = [event("2019-10-01", "torn knee ligament"), event("2019-08-01", "knee injury (date approximate)")]
        result = history.History(rows).summary(self.store, "p", 2020)
        self.assertEqual(result["episodes"], 0)

    def test_later_missing_archive_coverage_is_not_treated_as_healthy(self):
        for year in (2026, 2027):
            with self.assertRaisesRegex(ValueError, "missing coverage is not health"):
                history.History([]).summary(self.store, "p", year)

    def test_zero_target_outcomes_are_kept_in_both_models(self):
        modeler = research.Research(self.store, history.History([]), {"PTS": 1})
        for kind in research.KINDS:
            model = modeler.fit([2021], 10, kind)
            self.assertEqual(model["training_samples"], 1)
            self.assertEqual(model["zero_target_samples"], 1)
            prediction = modeler.predict(model, modeler.frame(2021)["p"])
            self.assertAlmostEqual(prediction["points"], 0)

    def test_features_and_training_ignore_future_production_and_injury_events(self):
        rows = [event("2018-08-01", "ankle injury"), event("2018-08-04", "returned to lineup", returned=True)]
        a = research.Research(self.store, history.History(rows), {"PTS": 1})
        changed = deepcopy(self.store.seasons); changed[2021] = {"p": season_player(82)}
        b = research.Research(Store(changed), history.History(rows+[event("2021-06-01", "torn ACL")]), {"PTS": 1})
        self.assertEqual(a.frame(2021), b.frame(2021))
        self.assertEqual(a.fit([2020], 10, "injury_output"), b.fit([2020], 10, "injury_output"))

    def test_output_and_games_bounds_and_short_season_target_normalization(self):
        store = Store({2020: {"p": season_player(36, 72)}})
        modeler = research.Research(store, history.History([]), {"PTS": 1})
        actual = modeler.actual("p", 2020)
        self.assertEqual(actual["games"], 41)
        self.assertEqual(actual["points"], 820)
        row = {"base": [1], "output": [1], "projection": {"fpg": 20}}
        model = {"kind": "base_games", "target": "games", "mean": [0], "scale": [1], "coefficients": [0, 10]}
        self.assertEqual(modeler.predict(model, row)["games"], 82)
        model.update(kind="base_output", target="points", coefficients=[0, -10])
        self.assertEqual(modeler.predict(model, row)["points"], 0)

    def test_corrupt_archive_fails_before_parsing_or_modeling(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"research-injury"; root.mkdir()
            (root/"transactions.json").write_text("[]")
            with self.assertRaisesRegex(ValueError, "hash changed"):
                history.load({"_data": folder})

    def test_command_has_no_execute_option(self):
        from basketball.cli import parser
        args = parser().parse_args(["research", "injury-backtest"])
        self.assertFalse(hasattr(args, "execute"))


if __name__ == "__main__": unittest.main()
