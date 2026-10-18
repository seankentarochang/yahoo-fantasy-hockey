"""Native slot occupancy, explicit refusal recovery and balanced expert picks."""
import copy
from unittest.mock import patch
import unittest

from basketball import availability, draft_balance
from basketball.cli import parser
from basketball.config import path, read_json, write_json
from basketball.draft_advisor import legal_choices
from basketball.draft_api import Room, reconcile, run
from basketball.model import Model
from test_basketball import athlete, snapshot
from test_basketball_draft_api import DraftApiTests, FakeSocket


class RefusingSocket(FakeSocket):
    def __init__(self, original, response='ERROR 1 Invalid+Selection.\n'):
        super().__init__(original.frames)
        self.response = response

    def send(self, command):
        if command == 'SELECT 1\n':
            self.sent.append(command)
            self.frames.append(self.response)
        else:
            super().send(command)


class DraftSafetyTests(unittest.TestCase):
    setUp = DraftApiTests.setUp
    room = DraftApiTests.room

    def refusing(self, response='ERROR 1 Invalid+Selection.\n'):
        room = self.room()
        room.socket = RefusingSocket(room.socket, response)
        return room

    def test_fixed_open_slot_blocks_forward_even_when_reassignment_would_fit(self):
        room = self.room()
        # A flexible player already occupies SG. A new PG could fit if moved,
        # but ESPN's remaining fixed slot is SG and that move has not happened.
        room.slots = {1: 'PG', 2: 'SG', 3: 'UTIL', 4: 'BE'}
        room.placements = {18: {1: 3, 3: 1, 4: 99}}
        model = room.model()
        self.assertIn(2, legal_choices(self.model, [2]))
        self.assertEqual(legal_choices(model, [2]), [])
        self.assertEqual(legal_choices(model, [3]), [3])
        with self.assertRaisesRegex(ValueError, 'remaining draft roster'):
            room.execute('pick', 2)
        self.assertFalse(any(s.startswith('SELECT ') for s in room.socket.sent))

    def test_native_slot_move_updates_occupancy_without_inventing_a_move(self):
        room = self.room()
        room.slots = {1:'PG', 2:'SG', 3:'BE'}
        room.placements = {18:{1:1}}
        before = room.context()
        room.consume('SLOT_CHANGED 18 1 1 3')
        self.assertEqual(room.model().snapshot['draft_constraints']['open_slots'], ['PG','SG'])
        self.assertNotEqual(before, room.context())
        with self.assertRaisesRegex(ValueError, 'cannot be reconciled'):
            room.consume('SLOT_CHANGED 18 1 1 2')

    def test_late_forward_passes_full_lineup_matching_but_cannot_fill_last_sg_slot(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['slots']={'PG':1,'SG':1,'SF':1,'PF':1,'C':1,'G':1,'F':1,'UTIL':2,'BE':3}
        positions=[('PG',),('SG','SF'),('PF',),('C',),('PG','SG'),('SF','PF'),
                   ('C',),('C',),('PF',),('SF',),('PF',),('SF','PF'),('SG',)]
        model=Model(cfg,snapshot([athlete(i,p) for i,p in enumerate(positions,1)]))
        write_json(path(cfg,'draft.json'),{'picks':[{'pick':i,'player':i,'team':18} for i in range(1,12)]})
        self.assertEqual(legal_choices(model,[12,13]),[12,13])
        model.snapshot['draft_constraints']={'open_slots':['SG'],'rejected':[]}
        self.assertEqual(legal_choices(model,[12,13]),[13])

    def test_init_uses_unique_native_slot_ids_and_current_placements_after_move(self):
        room=self.room()
        init=copy.deepcopy(room.init)
        league=init['league']
        league['draftRules']={}
        league['draftSlots']=[{'slotId':41,'slotCategoryId':1},{'slotId':42,'slotCategoryId':0}]
        league['draftPicks']=[{'playerId':1,'slotId':42,'teamId':18,'pickNumber':1,'bidAmount':0}]
        league['draftTeams'][0]['draftRosterItems']=[{'playerId':1,'slotId':41}]
        with patch('basketball.draft_api.Decoder.decode',return_value=init):
            room.consume('INIT AA==')
        self.assertEqual(room.placements[18],{41:1})
        self.assertEqual(room.model().snapshot['draft_constraints']['open_slots'],['PG'])
        self.assertEqual(legal_choices(room.model(),[2,3]),[2])
        league['draftSlots'].append({'slotId':41,'slotCategoryId':0})
        with patch('basketball.draft_api.Decoder.decode',return_value=init):
            with self.assertRaisesRegex(ValueError,'duplicate draft slots'):
                room.consume('INIT AA==')

    def test_explicit_refusal_is_durable_and_next_candidate_can_be_selected(self):
        room = self.refusing()
        result = room.execute('pick', 1)
        self.assertTrue(result['rejected'])
        self.assertFalse(result['verified'])
        self.assertIsNone(read_json(path(self.cfg,'draft-write.json')))
        self.assertFalse(read_json(path(self.cfg,'draft-receipts.json'), []))
        self.assertEqual(legal_choices(room.model(), [1,2]), [2])
        self.assertTrue(room.execute('pick', 2)['verified'])
        self.assertEqual([s for s in room.socket.sent if s.startswith('SELECT ')], ['SELECT 1\n','SELECT 2\n'])
        self.assertEqual(len(read_json(path(self.cfg,'draft-rejections.json'))), 1)
        self.assertEqual(len(read_json(path(self.cfg,'draft-receipts.json'))), 1)

    def test_watch_recovers_explicit_refusal_using_new_verified_expert_choice(self):
        room = self.refusing()
        args = parser().parse_args(['draft','watch','--strategy','expert','--source','rotowire','--execute'])
        original_execute, original_receive = room.execute, room.receive
        sent = room.socket.sent
        def execute(*args, **kwargs):
            result = original_execute(*args, **kwargs)
            if result.get('verified'):room.state = 2
            return result
        def board(model, source, limit=20):
            return {'players':[{'id':pid,'name':f'Player {pid}'} for pid in legal_choices(model,[1,2])],
                    'sources':[], 'timing':{}}
        with patch('basketball.draft_api.Room', return_value=room), patch.object(Room,'__enter__',return_value=room), \
             patch('basketball.draft_api.expert_board',side_effect=board), \
             patch('basketball.availability.check',return_value={'allowed':True}), \
             patch.object(room,'execute',side_effect=execute), \
             patch.object(room,'receive',side_effect=lambda timeout=1: original_receive(timeout) if room.socket.frames and room.state!=2 else False), \
             patch('builtins.print'):
            result = run(self.cfg,args)
        self.assertEqual(result['state'],'complete')
        self.assertEqual([s for s in sent if s.startswith('SELECT ')], ['SELECT 1\n','SELECT 2\n'])

    def test_full_frame_is_processed_and_actual_receipt_prevents_second_selection(self):
        room = self.refusing('ERROR 1 Invalid+Selection.\nSELECTED 18 1 0\nCLOCK 1 60000 2\n')
        self.assertTrue(room.execute('pick',1)['verified'])
        self.assertEqual(room.selecting,2)
        self.assertEqual(len(read_json(path(self.cfg,'draft-receipts.json'))),1)
        self.assertFalse(read_json(path(self.cfg,'draft-rejections.json'),[]))

    def test_unknown_errors_do_not_release_or_retry_intent(self):
        for message in ('ERROR 2 Invalid+Selection.', 'ERROR 1 Not+authorized.', 'ERROR 1 Invalid+Selection.+extra'):
            write_json(path(self.cfg,'draft-write.json'),None)
            room = self.refusing(message+'\n')
            with self.assertRaisesRegex(ValueError,'rejected a draft command'):
                room.execute('pick',1)
            self.assertEqual(read_json(path(self.cfg,'draft-write.json'))['player'],1)
            self.assertFalse(read_json(path(self.cfg,'draft-rejections.json'),[]))

    def test_unattributed_invalid_selection_is_not_recoverable(self):
        with self.assertRaisesRegex(ValueError,'rejected a draft command'):
            self.room().consume('ERROR 1 Invalid+Selection.')

    def test_crash_after_refusal_preserves_evidence_for_reconnect(self):
        room = self.refusing()
        original = room.refresh
        calls = []
        def refresh():
            calls.append(1)
            if len(calls)==3:raise ValueError('Disconnected at recovery barrier')
            original()
        with patch.object(room,'refresh',side_effect=refresh):
            with self.assertRaisesRegex(ValueError,'Disconnected'):
                room.execute('pick',1)
        self.assertEqual(read_json(path(self.cfg,'draft-write.json'))['server_rejection']['reason'],'invalid_selection')
        recovered = self.room()
        recovered.refresh()
        self.assertIsNone(reconcile(recovered))
        self.assertEqual(legal_choices(recovered.model(),[1,2]),[2])
        self.assertIsNone(reconcile(recovered))
        self.assertEqual(len(read_json(path(self.cfg,'draft-rejections.json'))),1)

    def test_refusal_is_scoped_to_context_and_clock_guard_still_applies(self):
        room = self.refusing()
        room.execute('pick',1)
        room.deadline = 0
        with self.assertRaisesRegex(ValueError,'25 seconds'):
            room.execute('pick',2)
        room.picks.append({'teamId':2,'playerId':3,'pickNumber':1,'bidAmount':0,'slotId':0})
        self.assertIn(1,legal_choices(room.model(),[1]))

    def test_autopick_must_be_confirmed_off(self):
        room = self.room()
        room.consume('AUTODRAFT 18 true')
        with self.assertRaisesRegex(ValueError,'Autopick disabled'):
            room.execute('pick',1)
        room.consume('AUTODRAFT 18 false')
        self.assertTrue(room.execute('pick',1)['verified'])
        with self.assertRaisesRegex(ValueError,'unknown Autopick'):
            room.consume('AUTODRAFT 18 unknown')


class BalanceTests(unittest.TestCase):
    setUp = DraftApiTests.setUp

    def model_and_rows(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['slots']={'PG':1,'SG':1,'SF':1,'PF':1,'C':1,'G':1,'F':1,'UTIL':2,'BE':3}
        cfg['draft']['balance']={'rank_gap':3,'start_round':2,'lookahead':32}
        players=[athlete(1,('PG',)),athlete(2,('SF',)),athlete(3,('SG',))]
        players += [athlete(i,('SF','PF')) for i in range(4,10)]
        model=Model(cfg,snapshot(players))
        write_json(path(cfg,'draft.json'),{'picks':[{'team':18,'player':1,'pick':1}]})
        rows=[{'id':i,'quality_order':i,'timing_tier':'before_next_turn' if i<4 else 'likely_available_next_turn',
               'published_expert_ranks':{'rotowire':50 if i==2 else 52 if i==3 else 100+i}} for i in range(2,10)]
        return model,rows

    def test_scarcity_prefers_guard_without_double_counting_flexibility(self):
        model,rows=self.model_and_rows()
        with patch('basketball.availability.check',return_value={'allowed':True}):
            selected,checks=draft_balance.verified_choice(model,rows)
        self.assertEqual(selected['id'],3)
        self.assertTrue(selected['balance']['changed'])
        self.assertEqual(draft_balance.coverage([athlete(1,('PG','SG'))],['PG','SG','G'],[1,1,1]),1)

    def test_first_round_rank_band_and_timing_tier_protect_best_expert(self):
        for mode in ('first','rank_gap','deferred'):
            model,rows=self.model_and_rows()
            if mode=='first':write_json(path(model.cfg,'draft.json'),{'picks':[]})
            if mode=='rank_gap':rows[1]['published_expert_ranks']['rotowire']=54
            if mode=='deferred':rows[1]['timing_tier']='likely_available_next_turn'
            with patch('basketball.availability.check',return_value={'allowed':True}):
                selected,_=draft_balance.verified_choice(model,rows)
            self.assertEqual(selected['id'],2,mode)

    def test_injured_or_unpublished_scarcity_alternative_cannot_jump_best(self):
        for mode in ('injured','unpublished'):
            model,rows=self.model_and_rows()
            if mode=='unpublished':rows[1]['published_expert_ranks']['rotowire']=None
            with patch('basketball.availability.check',side_effect=lambda cfg,p:{'allowed':p['id']!=3}):
                selected,_=draft_balance.verified_choice(model,rows)
            self.assertEqual(selected['id'],2,mode)


if __name__=='__main__':
    unittest.main()
