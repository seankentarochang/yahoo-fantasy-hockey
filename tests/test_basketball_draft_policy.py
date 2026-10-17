"""Next-turn demand, injury price and source identity regressions, without ESPN writes."""
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from basketball import availability
from basketball.config import load, read_json, write_json
from basketball.draft_timing import prioritize, window
from basketball.injury_returns import assess, catalog, estimate
from basketball.live_rankings import Cards, URL, collect, validate
from basketball.backtest import digest
from basketball.ranking_library import validate_rows
from basketball.draft_advisor import expert_board
from basketball.model import Model
from test_basketball import athlete, snapshot
import test_basketball_availability as availability_fixtures
import test_basketball_draft_api as api_fixtures


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = load()
        self.cfg['_data'] = self.tmp.name
        self.cfg['draft']['slot'] = 15
        self.players = [dict(athlete(i), draft_rank=i, active=True) for i in range(1, 220)]
        self.model = Model(self.cfg, snapshot(self.players))
        # At pick 47, two prior team selections and 46 total picks.
        self.picks = [{'pick': i, 'player': i, 'team': 18 if i in (15, 18) else 99} for i in range(1, 47)]
        self.save()

    def save(self):
        write_json(Path(self.tmp.name)/'draft.json', {'picks': self.picks})

    def test_kessler_is_deferred_at_47_and_becomes_urgent_at_50(self):
        candidates = [{'id': 69, 'espn_rank': 69}, {'id': 48, 'espn_rank': 48}, {'id': 49, 'espn_rank': 49}]
        urgent, deferred, timing = prioritize(self.model, candidates)
        self.assertEqual(timing['next_pick'], 50)
        self.assertEqual(timing['opponent_picks'], 2)
        self.assertEqual([p['id'] for p in urgent], [48, 49])
        self.assertEqual([p['id'] for p in deferred], [69])
        self.picks += [{'pick': i, 'player': i, 'team': 18 if i == 47 else 99} for i in range(47, 50)]
        self.save()
        urgent, _, timing = prioritize(self.model, [candidates[0]])
        self.assertEqual(timing['next_pick'], 79)
        self.assertEqual(urgent[0]['id'], 69)

    def test_forecast_counts_remaining_market_including_our_banned_targets(self):
        # Overall rank thresholds would incorrectly call #69 safe when #47-68
        # have already gone. Demand must come from the actual remaining pool.
        for p in self.model.players:
            if 47 <= p['id'] < 69:
                p['owner'] = 99
        urgent, _, _ = prioritize(self.model, [{'id': 69, 'espn_rank': 69}])
        self.assertEqual(urgent[0]['id'], 69)
        write_json(Path(self.tmp.name)/'draft-bans.json', {'version': 1, 'players': [{'id': 69, 'name': 'Our ban'}], 'teams': []})
        urgent, _, _ = prioritize(self.model, [{'id': 72, 'espn_rank': 72}])
        self.assertEqual(urgent, [])  # Opponents can still take #69.

    def test_final_pick_has_no_defer_rule_and_corrupt_history_fails(self):
        self.picks = [{'pick': i, 'player': i, 'team': 18 if i in (15,18,47,50,79,82,111,114,143,146,175) else 99}
                      for i in range(1, 178)]
        self.save()
        candidates = [{'id': 210, 'espn_rank': 210}]
        urgent, deferred, timing = prioritize(self.model, candidates)
        self.assertEqual(urgent, candidates)
        self.assertEqual(deferred, [])
        self.assertIsNone(timing['next_pick'])
        self.picks[0]['pick'] = 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            window(self.model)

    def test_confirmed_order_wins_over_stale_slot_and_consecutive_picks_do_not_defer(self):
        self.cfg['draft']['slot'] = 2
        self.model.snapshot['settings'] = {'draftSettings': {'pickOrder': [99]*14+[18,98]}}
        self.assertEqual(window(self.model)['next_pick'], 50)
        self.picks = []
        self.save()
        self.model.snapshot['settings']['draftSettings']['pickOrder'] = [99]*15+[18]
        candidates = [{'id': 210, 'espn_rank': 210}]
        self.assertEqual(prioritize(self.model, candidates)[0], candidates)

    def test_expert_board_prioritizes_market_demand_and_keeps_deferred_fallback(self):
        source = {'source': {'season': 2027, 'format': 'points', 'family': 'RotoWire', 'url': 'https://example.com'},
                  'status': 'prospective', 'rows': [{'name': 'Player 69', 'rank': 1}, {'name': 'Player 48', 'rank': 2}],
                  'retrieved_at': '2026-10-17T10:00:00Z', 'board_sha256': 'test'}
        root = Path(self.tmp.name)
        write_json(root/'ranking-library/boards/new-board.json', source)
        write_json(root/'draft-sources.json', {'rotowire': 'new-board'})
        with patch('basketball.draft_advisor.checked_board'):
            board = expert_board(self.model, limit=None)
        self.assertEqual(board['players'][0]['id'], 48)
        self.assertEqual(board['deferred'][0]['id'], 69)
        self.assertEqual(board['sources'][0]['source_id'], 'new-board')
        with patch('basketball.availability.check', side_effect=lambda cfg,p: {'id':p['id'], 'allowed':p['id']==69}):
            candidate, checks = availability.verified_choice(self.model, board['players'])
        self.assertEqual(candidate['id'], 69)
        self.assertTrue(all(c['id'] in (47,48,49) for c in checks[:-1]))
        (root/'draft-sources.json').unlink()
        with self.assertRaisesRegex(ValueError, 'selected current RotoWire'):
            expert_board(self.model)


class InjuryPolicyTests(unittest.TestCase):
    setUp = availability_fixtures.AvailabilityTests.setUp
    injury = availability_fixtures.AvailabilityTests.injury
    result = availability_fixtures.AvailabilityTests.result

    def enable(self):
        self.cfg['draft']['injury_policy'] = load()['draft']['injury_policy']
        timer = patch('basketball.injury_returns.now', return_value=self.at)
        timer.start()
        self.addCleanup(timer.stop)

    def round(self, number):
        write_json(Path(self.tmp.name)/'draft.json', {'picks': [{'team': self.cfg['team_id'], 'player': i, 'pick': i}
                                                            for i in range(1, number)]})

    def test_short_injury_is_eligible_without_review_or_roster_count_limit(self):
        self.enable()
        self.injury()
        self.round(4)
        result = self.result()
        self.assertEqual(result['status'], 'injury_eligible')
        self.assertTrue(result['allowed'])
        self.assertEqual(result['return_assessment']['expected_return'], '2026-10-25')

    def test_long_absence_is_late_round_target_and_season_out_never_allowed(self):
        self.enable()
        self.injury('OUT')
        row = self.report['injuries'][0]['injuries'][0]
        row['details']['returnDate'] = '2027-01-02'
        for number in (1,4,5,8):
            self.round(number)
            self.assertFalse(self.result()['allowed'])
        for number in (9,12):
            self.round(number)
            self.assertTrue(self.result()['allowed'])
        row['details']['fantasyStatus']['abbreviation'] = 'OFS'
        self.assertEqual(self.result()['status'], 'blocked')

    def test_unknown_overdue_bad_dates_and_team_conflicts_never_auto_clear(self):
        self.enable()
        self.injury('OUT')
        self.round(12)
        row = self.report['injuries'][0]['injuries'][0]
        for value in (None, 'TBD', '2026-10-01', '2027-05-01'):
            row['details']['returnDate'] = value
            self.assertFalse(self.result()['allowed'])
        row['details']['returnDate'] = '2026-10-25'
        self.player['status'] = 'SUSPENSION'
        self.assertFalse(self.result()['allowed'])
        self.player['status'] = 'ACTIVE'
        self.player['team'] = '2'
        self.assertFalse(self.result()['allowed'])

    def test_middle_rounds_allow_six_weeks_and_latest_estimate_is_conservative(self):
        self.enable()
        self.injury('OUT')
        row = self.report['injuries'][0]['injuries'][0]
        row['details']['returnDate'] = '2026-11-20'
        self.round(4)
        self.assertFalse(self.result()['allowed'])
        self.round(5)
        self.assertTrue(self.result()['allowed'])
        record = availability.injury_record(row)
        self.assertEqual(estimate([record, dict(record, return_date='2027-01-02')], self.at)['expected_return'], '2027-01-02')
        self.assertEqual(estimate([dict(record, return_date='2026-11-20T00:00:00.000+00:00')], self.at)['expected_return'], '2026-11-20')
        self.assertIsNone(estimate([record, dict(record, return_date=None)], self.at)['expected_return'])

    def test_catalog_is_sourced_and_stale_report_cannot_replace_it(self):
        self.injury()
        with patch('basketball.injury_returns.now', return_value=self.at):
            report = catalog(self.cfg, sources=self.source)
            self.assertEqual(report['players'][0]['expected_return'], '2026-10-25')
            self.assertIn('not a guaranteed', report['players'][0]['certainty'])
            self.report['timestamp'] = '2026-10-16T12:00:00Z'
            with self.assertRaisesRegex(ValueError, 'unverified'):
                catalog(self.cfg, sources=self.source)


class ExecutionPolicyTests(unittest.TestCase):
    setUp = api_fixtures.DraftApiTests.setUp
    room = api_fixtures.DraftApiTests.room

    def test_wrong_expert_choice_is_blocked_before_journal_and_send(self):
        room = self.room()
        with patch('basketball.draft_api.expert_board', return_value={'players':[{'id':2}], 'sources':[], 'timing':{}}), \
             patch('basketball.draft_api.availability.verified_choice', return_value=({'id':2}, [])):
            with self.assertRaisesRegex(ValueError, 'choice changed'):
                room.execute('pick', 1, expert_source='rotowire')
        self.assertFalse(any(s.startswith('SELECT ') for s in room.socket.sent))
        self.assertIsNone(read_json(Path(self.tmp.name)/'draft-write.json'))

    def test_expert_receipt_preserves_source_timing_and_candidate(self):
        room = self.room()
        expected = {'id':1, 'timing_tier':'before_next_turn'}
        with patch('basketball.draft_api.expert_board', return_value={'players':[expected], 'sources':[{'source_id':'updated'}], 'timing':{'next_pick':4}}), \
             patch('basketball.draft_api.availability.verified_choice', return_value=(expected, [])):
            room.execute('pick', 1, expert_source='rotowire')
        receipt = read_json(Path(self.tmp.name)/'draft-receipts.json')[0]
        self.assertEqual(receipt['selection']['candidate'], expected)
        self.assertEqual(receipt['selection']['timing']['next_pick'], 4)

    def test_expert_recheck_still_enforces_the_live_clock(self):
        room = self.room()
        def choose(*args):
            room.deadline = 0
            return {'id':1}, []
        with patch('basketball.draft_api.expert_board', return_value={'players':[{'id':1}], 'sources':[], 'timing':{}}), \
             patch('basketball.draft_api.availability.verified_choice', side_effect=choose):
            with self.assertRaisesRegex(ValueError, '25 seconds'):
                room.execute('pick', 1, expert_source='rotowire')
        self.assertFalse(any(s.startswith('SELECT ') for s in room.socket.sent))


class PublishedCardTests(unittest.TestCase):
    def test_published_card_keeps_overall_rank_and_ignores_position_rank_and_team(self):
        text = '<div class="rwcs-rank-row"><span class="rwcs-rank-num">36</span><span class="rwcs-rank-player"><span class="rwcs-pr">(C10)</span>Walker Kessler<span class="rwcs-team"> · LAL</span></span><span class="rwcs-rank-pos">C</span></div>'
        self.assertEqual(Cards(text).rows, [{'rank':36, 'name':'Walker Kessler', 'positions':[]}])
        with self.assertRaisesRegex(ValueError, 'Expected 200'):
            validate_rows(Cards(text).rows, {'count':200})

    def test_current_source_capture_is_pinned_and_does_not_overwrite_old_board(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = load()
            cfg['_data'] = folder
            text = '<title>2026-27 Fantasy Basketball Cheat Sheet for Points Leagues</title>'
            text += '<script>{"datePublished":"2026-10-16T12:00:00Z","dateModified":"2026-10-16T12:00:00Z"}</script>'
            text += ''.join(f'<div class="rwcs-rank-row"><span class="rwcs-rank-num">{i}</span><span class="rwcs-rank-player">Player {i}</span></div>' for i in range(1,201))
            response = BytesIO(text.encode())
            response.geturl = lambda: URL
            old = Path(folder)/'ranking-library/boards/rotowire-2027.json'
            write_json(old, {'original':'untouched'})
            with patch('basketball.live_rankings.urllib.request.urlopen', return_value=response):
                result = collect(cfg)
            self.assertEqual(result['published_rows'],200)
            self.assertEqual(read_json(old), {'original':'untouched'})
            self.assertEqual(read_json(Path(folder)/'draft-sources.json')['rotowire'],result['source'])
            root = Path(folder)/'ranking-library'
            board = read_json(root/'boards'/(result['source']+'.json'))
            # A source captured on draft morning is valid before 11, even
            # though the historical experiment cutoff was midnight.
            board['retrieved_at'] = '2026-10-18T14:30:00Z'
            board['board_sha256'] = digest({k:v for k,v in board.items() if k!='board_sha256'})
            with patch('basketball.live_rankings.now', return_value=datetime(2026,10,18,14,45,tzinfo=timezone.utc)):
                validate(cfg,root,board)
                board['retrieved_at'] = '2026-10-18T15:01:00Z'
                board['board_sha256'] = digest({k:v for k,v in board.items() if k!='board_sha256'})
                with self.assertRaisesRegex(ValueError,'before this draft'):
                    validate(cfg,root,board)


if __name__ == '__main__':
    unittest.main()
