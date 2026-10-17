"""Fixed NHL-style arithmetic, positional replacement and news-scope checks."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from basketball import value_board as value
from basketball.config import load, write_json
from basketball.empirical import Store, points

SCORING={"FGM":2,"FGA":-1,"FTM":1,"FTA":-1,"3PM":1,"REB":1,"AST":2,"STL":3,"BLK":3,"TO":-2,"PTS":1}


def row(games, multiplier=1):
    stats={"PTS":20,"FGM":7,"FGA":15,"FTM":4,"FTA":5,"3PM":2,"REB":5,"AST":4,"STL":1,"BLK":1,"TO":2,"3PA":5}
    return {"name":"Player 1","games":games,"minutes":games*30,"game_share":min(1,games/82),
            "stats":{k:v*games*multiplier for k,v in stats.items()}}


class ProjectionTests(unittest.TestCase):
    def test_comparison_commands_have_no_execute_mode(self):
        from basketball.cli import parser
        for action in ('value-backtest','value-rank'):
            args=parser().parse_args(['research',action])
            self.assertEqual(args.command,'research')
            self.assertEqual(args.action,action)
            self.assertFalse(hasattr(args,'execute'))

    def test_weighted_points_per_game_and_separate_games_average(self):
        data=Store({2025:{'1':row(40)},2026:{'1':row(80,2)}})
        result=value.projection(data,'1',2027,SCORING)
        expected=(.65*80*70+.35*40*35)/(.65*80+.35*40)
        self.assertAlmostEqual(result['fpg'],expected)
        self.assertEqual(result['games'],72)
        self.assertAlmostEqual(result['season_points'],expected*72)
        self.assertAlmostEqual(points(result['per_game'],SCORING),result['fpg'])

    def test_threshold_sample_discount_and_games_floors(self):
        self.assertIsNone(value.projection(Store({2026:{'1':row(19)}}),'1',2027,SCORING))
        result=value.projection(Store({2026:{'1':row(20)}}),'1',2027,SCORING)
        self.assertEqual(result['games'],40)
        self.assertAlmostEqual(result['fpg'],35*(.85+.15*20/60))
        # 100 combined games gives the NHL established-player floor.
        result=value.projection(Store({2025:{'1':row(82)},2026:{'1':row(18)}}),'1',2027,SCORING)
        self.assertEqual(result['games'],60)
        result=value.projection(Store({2025:{'1':row(82)},2026:{'1':row(82)}}),'1',2027,SCORING)
        self.assertEqual(result['games'],80)

    def test_missing_recent_season_is_carried_and_explicitly_flagged(self):
        result=value.projection(Store({2025:{'1':row(50)},2026:{}}),'1',2027,SCORING)
        self.assertTrue(result['missing_latest_season'])
        self.assertEqual(result['games'],50)
        self.assertAlmostEqual(result['fpg'],35*(.85+.15*50/60))

    def test_target_and_later_actuals_cannot_change_projection(self):
        seasons={2024:{'1':row(70)},2025:{'1':row(65)},2026:{'1':row(80,10)}}
        before=value.projection(Store(seasons),'1',2026,SCORING)
        altered=deepcopy(seasons);altered[2026]['1']=row(10,1000);altered[2027]={'1':row(82,10000)}
        self.assertEqual(before,value.projection(Store(altered),'1',2026,SCORING))


class ReplacementTests(unittest.TestCase):
    def test_depth_matches_full_league_and_excludes_ir(self):
        cfg=load();self.assertEqual(value.replacement_depth(cfg),{'PG':40,'SG':40,'SF':40,'PF':40,'C':32})
        cfg['slots']['IR']=999
        self.assertEqual(value.replacement_depth(cfg)['C'],32)
        cfg['slots']['Unknown']=1
        with self.assertRaisesRegex(ValueError,'Unsupported slot'):value.replacement_depth(cfg)

    def test_scarcity_can_reverse_raw_points_ranking(self):
        cfg={'teams':1,'slots':{'PG':1,'SG':1,'BE':5}}
        rows=[{'id':i,'primary':pos,'season_points':score} for i,(pos,score) in enumerate([
              ('PG',600),('PG',450),('PG',400),('SG',550),('SG',300),('SG',280)],1)]
        levels=value.replacement_levels(rows,cfg)
        value.attach_value(rows,levels)
        self.assertEqual(rows[0]['vor'],150);self.assertEqual(rows[3]['vor'],250)
        self.assertEqual(max(rows,key=lambda r:r['vor'])['id'],4)

    def test_small_groups_use_last_modeled_player_and_ties_are_stable(self):
        rows=[{'id':2,'primary':'C','season_points':500},{'id':1,'primary':'C','season_points':500}]
        levels=value.replacement_levels(rows,load())
        self.assertEqual(levels['C']['actual_depth'],2)
        self.assertEqual(levels['C']['player_id'],2)
        value.attach_value(rows,levels)
        self.assertEqual([r['vor'] for r in rows],[0,0])
        with self.assertRaisesRegex(ValueError,'replacement baseline'):
            value.attach_value([{'primary':'PG','season_points':400}],levels)


class AdjustmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.file=Path(self.tmp.name)/'adjustments.json'
        self.entry={'id':1,'games':70,'fpg_multiplier':1.1,'source':'https://example.com/team-report',
                    'observed_at':'2026-10-16T12:00:00-04:00','note':'Explicit researched adjustment'}
        self.save([self.entry])

    def save(self,entries):write_json(self.file,{'version':1,'season':2027,'players':entries})

    def test_current_overrides_never_apply_to_historical_seasons(self):
        self.assertEqual(value.adjustments(2026,'2025-10-01T12:00:00-04:00',self.file),{})
        self.assertEqual(value.adjustments(2027,'2026-10-17T12:00:00-04:00',self.file)[1]['games'],70)

    def test_future_naive_duplicate_and_invalid_numbers_fail(self):
        for change in [{'observed_at':'2026-10-18T12:00:00-04:00'},{'observed_at':'2026-10-16'},
                       {'games':-1},{'games':83},{'fpg_multiplier':float('nan')},{'source':'javascript:bad'}]:
            self.save([{**self.entry,**change}])
            with self.assertRaises(ValueError):value.adjustments(2027,'2026-10-17T12:00:00-04:00',self.file)
        self.save([self.entry,self.entry])
        with self.assertRaises(ValueError):value.adjustments(2027,'2026-10-17T12:00:00-04:00',self.file)

    def test_notes_do_not_change_production_and_injury_is_a_cap_not_subtraction(self):
        forecast=value.projection(Store({2026:{'1':row(70)}}),'1',2027,SCORING)
        unchanged=value.apply_adjustment(forecast,{'note':'New team'})
        self.assertEqual(unchanged['fpg'],forecast['fpg'])
        self.assertEqual(unchanged['games'],forecast['games'])
        adjusted=value.apply_adjustment(forecast,{'games':82,'fpg_multiplier':1.2},40)
        self.assertEqual(adjusted['games'],40)
        self.assertAlmostEqual(adjusted['season_points'],forecast['fpg']*1.2*40)
        self.assertEqual(value.apply_adjustment(forecast,injury_cap=80)['games'],forecast['games'])
        self.assertEqual(forecast['games'],70)


if __name__=='__main__':unittest.main()
