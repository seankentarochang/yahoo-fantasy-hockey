"""Focused comparison-model/data-quality tests. No authenticated ESPN access."""
import csv
import hashlib
import io
from pathlib import Path
import tempfile
import unittest

from basketball import research_board as board, research_data as datasets
from basketball.backtest import digest
from basketball.config import read_json, write_json


STATS={"PTS":20,"FGM":7,"FGA":15,"FTM":4,"FTA":5,"3PM":2,"REB":5,"AST":4,"STL":1,"BLK":1,"TO":2}
SCORING={"FGM":2,"FGA":-1,"FTM":1,"FTA":-1,"3PM":1,"REB":1,"AST":2,"STL":3,"BLK":3,"TO":-2,"PTS":1}


def fixture():
    player={"id":1,"name":"Test Player","team":"1","eligible":["PG"],"active":True,"draft_rank":50,
            "splits":[{"season":2027,"source":1,"stats":{**{k:v*70 for k,v in STATS.items()},"GP":70,"MIN":2100}}]}
    inputs={"season":2027,"as_of":"2026-10-17T12:00:00+00:00","scoring":SCORING,
            "snapshot":{"players":[player],"games":{"1":[{"id":i,"date":f"2027-01-{i:02}"} for i in range(1,31)]}},
            "history":{},"rosters":{"1":{"team":"1","team_name":"Test Team","abbreviation":"TST","status":"active"}},
            "injuries":{"players":[]},"context":{"team_role_changes":[]},"comparison_ranks":{"1":20},
            "bans":{"version":1,"players":[],"teams":[]},"public_projections":[],"bref_projections":[],
            "fantasypros_opportunities":[],"darko":{"players":[],"used_in_model":False}}
    return player,inputs


def table(rows):
    return '<table>'+''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)+'</table>'


class SourceParsingTests(unittest.TestCase):
    def test_bref_full_projection_only_per_minute_with_explicit_shooting(self):
        header=["Rk","Player","Type","FG","FGA","3P","3PA","FT","FTA","ORB","TRB","AST","STL","BLK","TOV","PF","PTS","FG%","3P%","FT%"]
        row=[1,"Player","Projected",7,15,2,5,4,5,1,5,4,1,1,2,2,20,.467,.4,.8]
        rows=[header]+[[i,f"Player {i}"]+row[2:] for i in range(400)]
        text='2026-27 Simple Projection System'+table(rows+[list(row[:2])+["2025-26"]+row[3:]])
        projections=board.bref_projections(text,2027)
        self.assertEqual(len(projections),400)
        self.assertAlmostEqual(projections[0]["rates"]["FGA"],15/36)
        with self.assertRaisesRegex(ValueError,'season'):
            board.bref_projections(text,2026)
        with self.assertRaisesRegex(ValueError,'columns'):
            board.bref_projections(text.replace('<td>FGA</td>','<td>Unknown</td>'),2027)
        with self.assertRaisesRegex(ValueError,'Invalid'):
            board.bref_projections(text.replace('<td>15</td>','<td>1</td>'),2027)

    def test_fantasypros_uses_only_games_minutes_not_rounded_shooting(self):
        header=["Player","PTS","REB","AST","BLK","STL","FG%","FT%","3PM","GP","MIN","TO"]
        rows=[header]+[[f'Player {i} (WAS - PG)',1400,350,280,70,70,'.467','.8',140,70,'2,100',140] for i in range(200)]
        text='2026-27 Projections Consensus last updated Oct 16, 2026'+table(rows)
        result,date=board.fantasypros_opportunities(text,2027)
        self.assertEqual(date,'Oct 16, 2026')
        self.assertEqual(result[0],{'name':'Player 0','team':'WAS','games':70,'minutes':30})
        self.assertNotIn('stats',result[0])
        with self.assertRaisesRegex(ValueError,'Invalid'):
            board.fantasypros_opportunities(text.replace('<td>70</td>','<td>0</td>'),2027)

    def test_date_and_ambiguous_identity_guard(self):
        captured='2026-10-17T12:00:00+00:00'
        board.verify_public_date('Oct 16, 2026','%b %d, %Y',captured)
        for value in ['Oct 18, 2026','Jul 26, 2026']:
            with self.assertRaisesRegex(ValueError,'date'):
                board.verify_public_date(value,'%b %d, %Y',captured)
        player,inputs=fixture();inputs['rosters']['1']['abbreviation']='WSH'
        matched,unmatched=board.match_outside([{'name':'Test Player','team':'WAS'}],inputs,True)
        self.assertEqual(list(matched),[1]);self.assertFalse(unmatched)
        inputs['snapshot']['players'].append(dict(player,id=2))
        matched,unmatched=board.match_outside([{'name':'Test Player','team':'WAS'}],inputs,True)
        self.assertFalse(matched);self.assertEqual(unmatched,['Test Player'])


class ForecastTests(unittest.TestCase):
    def test_hand_calculated_sources_opportunity_and_exact_league_scoring(self):
        player,inputs=fixture()
        # BRef rates double the baseline; it has no games/minutes vote.
        bref={'rates':{k:v/15 for k,v in STATS.items()}}
        outside={'games':60,'minutes':20}
        result=board.forecast(player,inputs,bref=bref,opportunities=outside)
        self.assertEqual(result['minutes'],25);self.assertEqual(result['games'],65)
        for k in STATS:self.assertAlmostEqual(result['per_game'][k],STATS[k]*1.25)
        expected=sum(v*SCORING[k] for k,v in STATS.items())*1.25
        self.assertAlmostEqual(result['fpg'],expected)
        self.assertAlmostEqual(result['season_points'],expected*65)
        self.assertEqual(result['forward_sources'],['ESPN','Basketball Reference'])
        self.assertEqual(result['playing_time_sources'],['ESPN','FantasyPros'])
        self.assertEqual(result['history_weight'],0)

    def test_rank_order_and_target_season_actuals_cannot_influence_forecast(self):
        player,inputs=fixture();before=board.forecast(player,inputs)
        player['draft_rank']=1;inputs['comparison_ranks']['1']=999
        player['splits'].append({'season':2027,'source':0,'stats':{**{k:99999 for k in STATS},'GP':82,'MIN':3000}})
        after=board.forecast(player,inputs)
        for k in ['fpg','games','season_points','per_game','history_weight']:
            self.assertEqual(before[k],after[k])

    def test_durability_absences_after_debut_and_role_history_cap(self):
        player,inputs=fixture()
        inputs['history']={'2026':{'1':{'minutes':2100,'team':'1','stats':{**{k:v*70 for k,v in STATS.items()},'GP':70}}},
                           '2024':{'1':{'minutes':2100,'team':'1','stats':{**{k:v*70 for k,v in STATS.items()},'GP':70}}}}
        result=board.forecast(player,inputs)
        self.assertAlmostEqual(result['historical_games'],49)
        self.assertAlmostEqual(result['games'],.75*70+.25*49)
        inputs['history']['2026']['1']['team']='2'
        self.assertEqual(board.forecast(player,inputs)['history_weight'],.35)
        inputs['history'].pop('2024')
        self.assertEqual(board.forecast(player,inputs)['historical_games'],70)

    def test_injury_cap_does_not_subtract_already_discounted_games(self):
        player,inputs=fixture()
        injury={'id':1,'out_for_season':False,'days_out':90,'expected_return':'2027-01-10'}
        inputs['injuries']['players']=[injury]
        result=board.forecast(player,inputs)
        # 21 dated games + 52 unassigned; cap 73 exceeds baseline 70.
        self.assertEqual(result['injury_opportunity_cap'],73)
        self.assertEqual(result['games'],70)
        injury['expected_return']='2027-01-30'
        self.assertEqual(board.forecast(player,inputs)['games'],53)
        injury['days_out']=None;injury['expected_return']=None
        self.assertIn('Unknown or overdue injury return',board.forecast(player,inputs)['flags'])
        injury['out_for_season']=True
        self.assertIsNone(board.forecast(player,inputs))

    def test_incomplete_forward_never_falls_back_to_actuals_and_ban_marked(self):
        player,inputs=fixture()
        inputs['bans']['players']=[{'id':1,'name':'Test Player'}]
        self.assertIn('Player ban',board.forecast(player,inputs)['ban'])
        player['splits'][0]['stats'].pop('FTA')
        self.assertIsNone(board.forecast(player,inputs))

    def test_reproducible_build_capture_tampering_inactive_and_unsupported_scoring(self):
        player,inputs=fixture()
        inputs['snapshot']['players'].append(dict(player,id=2,name='Retired Player',active=False))
        with tempfile.TemporaryDirectory() as directory:
            cfg={'_data':directory,'season':2027,'scoring':SCORING}
            root=Path(directory)/'research-board';root.mkdir()
            capture=root/'source.raw';capture.write_bytes(b'public data')
            manifest={'parameters':board.PARAMETERS,'inputs_sha256':digest(inputs),'records':[{'file':'source.raw','sha256':hashlib.sha256(capture.read_bytes()).hexdigest()}]}
            write_json(root/'manifest.json',manifest);write_json(root/'inputs.json',inputs)
            board.build(cfg);first=(root/'rankings.json').read_bytes();board.build(cfg)
            self.assertEqual(first,(root/'rankings.json').read_bytes())
            report=read_json(root/'rankings.json')
            self.assertTrue(report['comparison_only']);self.assertFalse(report['performance_validated'])
            self.assertEqual(report['ranked_players'],1)
            self.assertEqual(report['excluded'][0]['name'],'Retired Player')
            capture.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'capture changed'):board.build(cfg)
            capture.write_bytes(b'public data')
            inputs['scoring']['DD']=1;cfg['scoring']={**inputs['scoring']}
            manifest['inputs_sha256']=digest(inputs)
            write_json(root/'manifest.json',manifest);write_json(root/'inputs.json',inputs)
            with self.assertRaisesRegex(ValueError,'scoring components'):board.build(cfg)


def game_csv(rows):
    fields=list(datasets.FIELDS.values())+['season','season_type_id','game_id','person_id','team_id','minutes','comment']
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode()


class GameDataTests(unittest.TestCase):
    def game(self,**values):
        return {**{v:STATS[k] for k,v in datasets.FIELDS.items()},'season':'2026','season_type_id':'2',
                'game_id':'0022500001','person_id':'NBA123','team_id':'NBA1','minutes':'23:60','comment':'',**values}

    def test_season_and_game_types_dnp_and_rollovers(self):
        rows=[self.game(),self.game(person_id='NBA124',minutes='',comment='DNP - Injury/Illness'),
              self.game(person_id='NBA125',game_id='0062500001',season_type_id='6'),
              self.game(person_id='NBA126',minutes='',**{v:0 for v in datasets.FIELDS.values()})]
        result=datasets.audit(game_csv(rows),2026)
        self.assertEqual(result['played_rows'],1);self.assertEqual(result['dnp_rows'],1)
        self.assertEqual(result['minute_second_rollovers'],1);self.assertEqual(result['unclassified_zero_stat_rows'],1)
        self.assertEqual(result['excluded_other_game_types'],1);self.assertEqual(result['games'],1)
        self.assertFalse(result['forecast_data'])

    def test_duplicates_wrong_season_and_invalid_actuals_fail(self):
        for rows,pattern in [([self.game(),self.game()],'duplicate'),([self.game(season='2025')],'season'),
                             ([self.game(field_goals_made=100)],'box score')]:
            with self.assertRaisesRegex(ValueError,pattern):datasets.audit(game_csv(rows),2026)


if __name__=='__main__':unittest.main()
