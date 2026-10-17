"""Chronological isolation, coherent predictions and paired draft regressions."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

import numpy as np

from basketball import empirical as e, empirical_draft as draft
from basketball.config import active_slots
from basketball.planner import assign, legal_roster

SCORING={"FGM":2,"FGA":-1,"FTM":1,"FTA":-1,"3PM":1,"REB":1,"AST":2,"STL":3,"BLK":3,"TO":-2,"PTS":1}


def row(pid, minutes=1800):
    counts={"PTS":20,"FGM":7,"FGA":15,"FTM":4,"FTA":5,"3PM":2,"3PA":5,"REB":5,"AST":4,"STL":1,"BLK":1,"TO":2}
    return {"id":str(pid),"name":f"Player {pid}","games":60,"game_share":60/82,
            "minutes":minutes,"stats":{k:v*60 for k,v in counts.items()}}


def store():
    return e.Store({year:{str(pid):row(pid,1500+50*pid+10*(year-2017)) for pid in range(1,7)} for year in range(2017,2027)})


class RateModelTests(unittest.TestCase):
    def test_forecast_features_cannot_read_target_or_later_outcomes(self):
        history=store();before=history.features('1',2025)
        altered=deepcopy(history.seasons)
        for year in [2025,2026]:
            altered[year]['1']['minutes']=1e8
            altered[year]['1']['stats']['PTS']=1e9
            altered[year]['999']=row(999)
        self.assertEqual(before,e.Store(altered).features('1',2025))
        self.assertNotIn('player999',e.Store(altered).identities(2025))

    def test_fitting_uses_only_registered_target_years(self):
        history=store();first=e.fit(history,[2020,2021,2022,2023],10)
        altered=deepcopy(history.seasons)
        for year in [2024,2025,2026]:
            for player in altered[year].values():player['stats']['AST']=999999
        second=e.fit(e.Store(altered),[2020,2021,2022,2023],10)
        self.assertEqual(first,second)
        self.assertEqual(first['training_samples'],24)
        self.assertEqual(first['training_years'],[2020,2021,2022,2023])

    def test_clipped_components_preserve_scoring_identities(self):
        stats=e.box_score([.4,.2,.15,.2,.1,-.2,.05,.1,1.5,-.5,.8])
        self.assertEqual(stats['STL'],0);self.assertEqual(stats['3PM'],0)
        self.assertLessEqual(stats['FGM'],stats['FGA'])
        self.assertLessEqual(stats['FTM'],stats['FTA'])
        self.assertAlmostEqual(stats['PTS'],2*stats['FGM']+stats['3PM']+stats['FTM'])
        with self.assertRaisesRegex(ValueError,'components'):e.box_score([float('nan')]*11)

    def test_historical_baseline_and_workload_hand_calculation(self):
        history=store();p=history.seasons[2026]['1']
        expected=e.points(p['stats'],SCORING)/p['minutes']
        self.assertAlmostEqual(e.points(history.baseline('1',2027,'last_season'),SCORING),expected)
        _,games=history.workload('1',2027)
        self.assertAlmostEqual(games,60)
        # Missing year after an observed appearance contributes zero durability.
        del history.seasons[2025]['1']
        self.assertAlmostEqual(history.workload('1',2027)[1],42)
        # The same missing year before first appearance is not an absence.
        for year in range(2017,2026):history.seasons[year].pop('1',None)
        self.assertAlmostEqual(history.workload('1',2027)[1],60)

    def test_paired_rate_cohort_and_current_projection_repeatability(self):
        history=store();model=e.fit(history,[2020,2021,2022,2023],10)
        metrics=e.evaluate_rates(history,model,2025,SCORING)
        self.assertEqual({v['players'] for v in metrics.values()},{6})
        values=e.predict(model,history.features('1',2027))
        self.assertTrue(all(np.isfinite(v) and v>=0 for v in values.values()))
        self.assertEqual(values,e.predict(model,history.features('1',2027)))
        with self.assertRaisesRegex(ValueError,'scoring component'):e.points(values,{'TD':1})

    def test_ambiguous_names_do_not_join_different_nba_ids(self):
        history=store();history.seasons[2024]['2']['name']='Player 1'
        self.assertNotIn('player1',history.identities(2025))


class DraftTests(unittest.TestCase):
    def test_fallback_players_keep_market_slots(self):
        self.assertEqual(draft.anchored_order([1,2,3,4],{1:10,3:30,4:40}),[4,2,3,1])

    def test_next_turn_uses_remaining_market_and_final_pick_has_no_limit(self):
        legal=lambda roster,pid:True
        order=[5,4,3,2,1];market=[1,2,3,4,5]
        self.assertEqual(draft.choose(order,legal,[],{1},market,2),3)
        self.assertEqual(draft.choose(order,legal,[],{1},market,None),5)
        self.assertEqual(draft.choose(order,lambda roster,pid:pid>3,[],{1},market,2),5)

    def test_small_snake_preserves_roster_coverage_and_records_next_turn(self):
        cfg={'teams':2,'slots':{'PG':1,'UTIL':1},'position_limits':{}}
        players={pid:{'id':pid,'name':str(pid),'primary':'PG','eligible':['PG','UTIL'],'slot':'BE'} for pid in range(1,9)}
        model=SimpleNamespace(cfg=cfg,by_id=players)
        def legal(roster,pid):
            prospective=[players[p] for p in (*roster,pid)]
            return legal_roster(prospective,cfg) and len(active_slots(cfg))-len(assign(prospective,active_slots(cfg)))<=2-len(prospective)
        roster,trace=draft.simulate(model,2,list(range(8,0,-1)),{1:list(players),2:list(players)},list(players),legal,True)
        self.assertEqual(roster,[8,7]);self.assertEqual([p['pick'] for p in trace],[2,3])
        self.assertEqual(trace[0]['opponent_picks_to_next'],0)
        self.assertIsNone(trace[-1]['opponent_picks_to_next'])

    def test_scoring_absent_target_player_is_zero_not_removed_from_cohort(self):
        history=store();model=SimpleNamespace(cfg={'scoring':SCORING},by_id={1:{'name':'Player 1'},999:{'name':'Absent'}})
        result=draft.score_roster([1,999],model,history,2026,{1:'1',999:'999'})
        self.assertEqual(result['total_points'],e.points(history.seasons[2026]['1']['stats'],SCORING))
        self.assertEqual(result['zero_games'],1)

    def test_summaries_compare_identical_seed_and_slot_pairs(self):
        rows=[]
        for slot,base in [(1,100),(2,200)]:
            for policy,total in [('espn',base),('learned_total',base*1.1)]:
                rows.append({'season':2026,'seed':-1,'slot':slot,'policy':policy,'total_points':total,'modeled_pick_share':1,'zero_games':0})
        result=draft.summarize(rows)['2026']['learned_total']
        self.assertAlmostEqual(result['mean_gain_pct_vs_espn'],10)
        self.assertEqual(result['paired_win_rate'],1)


if __name__=='__main__':unittest.main()
