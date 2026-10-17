"""Historical-source eligibility, equal publisher votes and paired summaries."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from basketball import expert_boards as expert
from basketball.backtest import digest
from basketball.config import write_json


def yahoo_payload():
    import json
    data = {"sport": "NBA", "year": "2023", "week": "0", "type": "Draft - Points", "ranking_type_name": "draft",
            "scoring": "PTS", "total_experts": 1, "expert_names": {"3793": "Dan Titus"},
            "last_updated_ts": int(datetime(2023, 10, 18, tzinfo=timezone.utc).timestamp()),
            "expert_pub": {"3793": "2023-10-18 00:00:00"}, "count": 2,
            "players": [{"player_name": "Player One", "experts": {"3793": "1"}, "rank_ecr": "1"},
                        {"player_name": "Player Two", "experts": {"3793": "2"}, "rank_ecr": "2"}]}
    return data, lambda value: "FPW.rankingsCB("+json.dumps(value)+");"


def source(sid, family, basis="published expert order", day="2023-10-01"):
    return {"id": sid, "family": family, "basis": basis,
            "date_evidence": {"datePublished": day+"T00:00:00+00:00"}}


class ExpertBoardTests(unittest.TestCase):
    def test_yahoo_rank_fields_exclude_dynamic_current_metadata(self):
        payload, encode = yahoo_payload()
        payload["players"][0].update(player_team_id="FUTURE", player_positions="FUTURE", player_nbacom_id="future")
        rows, _, rejected = expert.yahoo_board(encode(payload), 2024)
        self.assertIsNone(rejected)
        self.assertEqual(rows[0], {"rank": 1, "name": "Player One", "positions": []})

    def test_widget_updated_after_cutoff_is_quarantined_even_if_article_is_old(self):
        payload, encode = yahoo_payload()
        payload["last_updated_ts"] = int(datetime(2023, 10, 24, tzinfo=timezone.utc).timestamp())
        rows, _, reason = expert.yahoo_board(encode(payload), 2024)
        self.assertEqual(rows, [])
        self.assertIn("after", reason)

    def test_wrong_season_format_or_expert_cannot_enter_yahoo_results(self):
        payload, encode = yahoo_payload()
        for field, value in (("year", "2024"), ("scoring", "HIGHSCORE"), ("week", "1"),
                             ("ranking_type_name", "ros"), ("expert_names", {"3793": "Other"})):
            with self.assertRaises(ValueError): expert.yahoo_board(encode({**payload, field: value}), 2024)
        payload["players"][0]["rank_ecr"] = "2"
        with self.assertRaisesRegex(ValueError, "conflicting"): expert.yahoo_board(encode(payload), 2024)

    def test_static_adapters_extract_only_contiguous_numbered_rankings(self):
        metadata = '<script type="application/ld+json">{"datePublished":"2023-08-12T00:00:00+00:00","dateModified":"2023-10-12T00:00:00+00:00"}</script>'
        table = '<title>Points Leagues Rankings</title>'+metadata+'<table><tr><th>RANK</th><th>PLAYER</th><th>TEAM</th><th>POS</th></tr>'
        table += ''.join(f'<tr><td>{i}</td><td>Player {i}</td><td>X</td><td>C</td></tr>' for i in range(1, 51))+'</table>'
        rows, _ = expert.static_board(table, "rotoballer")
        self.assertEqual(len(rows), 50)
        with self.assertRaises(ValueError): expert.static_board(table.replace('<td>50</td>', '<td>49</td>'), "rotoballer")
        page = '<title>2024-25 Fantasy Basketball Points League Rankings</title>'+metadata
        page += ''.join(f'{i}.<strong>Player {i}</strong><br/>' for i in range(1, 201))
        self.assertEqual(len(expert.static_board(page, "fantrax")[0]), 200)

    def test_partial_board_falls_back_to_espn_without_dropping_players(self):
        self.assertEqual(expert.complete([1, 2, 3, 4], {4: 1, 2: 2}), [4, 2, 1, 3])

    def test_known_full_name_and_suffix_aliases_resolve_to_existing_id(self):
        identities = {"camthomas": {4432174}, "xaviertillman": {4277964}}
        for name, expected in (("Cameron Thomas", 4432174), ("Xavier Tillman Sr.", 4277964)):
            canonical = expert.ALIASES.get(expert.key(name), name)
            self.assertEqual(expert.resolve_name(canonical, identities, identities), expected)

    def test_publisher_variants_get_one_consensus_vote(self):
        sources = [source("espn", "ESPN"), source("rw_early", "RotoWire"),
                   source("rw_total", "RotoWire", "projected total points", "2023-10-10"),
                   source("rw_pergame", "RotoWire", "projected points per game", "2023-10-15")]
        ranks = {"espn": {1: 1, 2: 2, 3: 3}, "rw_early": {3: 1, 2: 2, 1: 3},
                 "rw_total": {2: 1, 1: 2, 3: 3}, "rw_pergame": {3: 1, 1: 2, 2: 3}}
        policies = expert.policies_for([1, 2, 3], ranks, sources, None)
        self.assertEqual(policies["consensus"]["sources"], ["espn", "rw_total"])
        self.assertEqual(policies["consensus"]["order"], [1, 2, 3])
        self.assertIn("rw_pergame", policies)

    def test_depth_uses_published_rank_not_first_matched_players(self):
        sources = [source("espn", "ESPN"), source("other", "Other")]
        ranks = {"espn": {1: 1, 2: 2, 3: 3}, "other": {3: 1, 2: 51}}
        policy = expert.policies_for([1, 2, 3], ranks, sources, 50)["other"]
        self.assertEqual(policy["coverage"], {3})
        self.assertEqual(policy["order"], [3, 1, 2])

    def test_timing_changes_selection_rule_but_preserves_board_order(self):
        sources = [source("espn", "ESPN"), source("other", "Other")]
        policies = expert.policies_for([1, 2], {"espn": {1: 1, 2: 2}, "other": {2: 1, 1: 2}}, sources, None)
        self.assertEqual(policies["other"]["order"], policies["other_next_turn"]["order"])
        self.assertFalse(policies["other"]["timing"])
        self.assertTrue(policies["other_next_turn"]["timing"])

    def test_paired_results_use_the_correct_field_depth_and_slot_baseline(self):
        rows = []
        for field, base in (("espn", 1000), ("consensus", 2000)):
            for policy, total in (("espn", base), ("other", base+100)):
                rows.append({"season": 2025, "field": field, "depth": "full", "seed": -1, "slot": 1,
                             "policy": policy, "total_points": total, "zero_games": 0, "covered_pick_share": .5})
        summaries = expert.summaries(rows)
        self.assertAlmostEqual(next(r for r in summaries if r["field"] == "espn" and r["policy"] == "other")["mean_gain_pct_vs_espn"], 10)
        self.assertAlmostEqual(next(r for r in summaries if r["field"] == "consensus" and r["policy"] == "other")["mean_gain_pct_vs_espn"], 5)

    def test_catalog_rejects_changed_capture_bytes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/"research-experts"; (root/"captures").mkdir(parents=True)
            file = root/"captures/source.html"; file.write_bytes(b"original")
            catalog = {"captures": [{"file": "source.html", "sha256": hashlib.sha256(b"original").hexdigest()}]}
            write_json(root/"catalog.json", catalog); write_json(root/"catalog-lock.json", {"sha256": digest(catalog)})
            self.assertEqual(expert.locked_catalog({"_data": folder}), catalog)
            file.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "changed"): expert.locked_catalog({"_data": folder})

    def test_research_commands_have_no_execution_flag(self):
        from basketball.cli import parser
        for action in ("expert-collect", "expert-backtest"):
            self.assertFalse(hasattr(parser().parse_args(["research", action]), "execute"))


if __name__ == "__main__": unittest.main()
