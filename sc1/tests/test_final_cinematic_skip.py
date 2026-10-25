"""Execute the two revised endings as ordinary CHK triggers, without a game."""
import unittest

from sc1.native_campaign import build_all_campaigns as b,campaign_objectives
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs,acts


def fixture(mission):
    spec=next(x for x in b.roster_specs() if x['mission_id']==mission)
    path=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path']
    source=b.CHK(path.read_bytes());row=b.metadata(spec,source,path)
    output=b.CHK(source.save());correction=campaign_objectives.apply(output,row)
    progression=b.patch_progression(output,row)
    return source,output,correction,progression


class FinalCinematicSkipTests(unittest.TestCase):
    def test_insurgent_final_battle_finishes_without_any_cinematic_actor(self):
        source,output,_,p=fixture(407);ts=b.triggers(output)
        event=ts[p['original_trigger_indices'][8]];route=p['routes'][0]
        latch=ts[route['goal_trigger_index']];ending=ts[route['ending_trigger_index']]
        self.assertEqual(cs(event),cs(b.triggers(source)[8]))
        m=OrdinaryTriggerMachine()
        m.values[3,7,79,9,0]=1
        self.assertFalse(m.run(event));self.assertFalse(m.run(latch))
        # Either earlier illusion can die without completing the final battle.
        for illusion in (4,5):
            self.assertTrue(m.run(ts[p['original_trigger_indices'][illusion]]))
            self.assertTrue(m.run(ts[p['original_trigger_indices'][6]]))
            self.assertFalse(m.run(event));self.assertFalse(m.run(latch))
        m.events.clear();m.clock_ms=0
        m.values[3,7,79,9,0]=0
        self.assertTrue(m.run(event))
        self.assertEqual(m.events,[('switch',9,True),('switch',10,True)])
        self.assertTrue(m.run(latch));self.assertFalse(m.run(latch))
        self.assertEqual(m.deaths[11,223],1);self.assertEqual(m.deaths[11,226],1)
        self.assertEqual([a[26] for a in acts(ending)],[1])
        # Neither actors, arrival switches, nor any time delay is needed.
        for ready,ack in ((False,False),(False,True),(True,False)):
            m.switches[242]=ready;m.switches[243]=ack
            self.assertFalse(m.run(ending));self.assertFalse(m.victory)
        m.switches[242]=m.switches[243]=True;m.events.clear()
        self.assertTrue(m.run(ending));self.assertEqual(m.events,[('victory',)])
        self.assertEqual(m.clock_ms,0)

    def test_insurgent_defeat_remains_active_before_goal_and_suppressed_after(self):
        _,output,_,p=fixture(407);ts=b.triggers(output)
        defeat=ts[p['original_trigger_indices'][3]]
        event=ts[p['original_trigger_indices'][8]]
        m=OrdinaryTriggerMachine();self.assertTrue(m.eligible(defeat))
        self.assertTrue(m.run(event));self.assertFalse(m.eligible(defeat))

    def test_removed_scenes_have_no_actions_even_if_old_switches_are_set(self):
        for mission in (206,407):
            with self.subTest(mission=mission):
                _,output,receipt,p=fixture(mission);ts=b.triggers(output)
                m=OrdinaryTriggerMachine();m.switches={i:True for i in range(256)}
                for index in receipt['removed_cinematic_triggers']:
                    t=ts[p['original_trigger_indices'][index]]
                    self.assertEqual(cs(t),[b.cond(23)])
                    self.assertEqual(acts(t),[]);self.assertFalse(m.run(t))
                self.assertEqual(p['middle']['kind'],'original_hostile_force_combat_progress')
                self.assertTrue(p['middle']['goal_catches_up_if_bypassed'])

    def test_zerg6_goal_and_saved_victory_need_no_tassadar_or_cinematic_switch(self):
        _,output,_,p=fixture(206);ts=b.triggers(output);route=p['routes'][0]
        latch=ts[route['goal_trigger_index']];ending=ts[route['ending_trigger_index']]
        m=OrdinaryTriggerMachine();m.values[12,0,0,0,0]=1;m.values[2,3,51,0,0]=1
        m.values[2,19,231,0,0]=1;self.assertFalse(m.run(latch))
        m.values[2,19,231,0,0]=0;m.values[2,3,51,0,0]=0;self.assertFalse(m.run(latch))
        m.values[2,3,51,0,0]=1;m.values[2,19,229,0,0]=100
        self.assertTrue(m.run(latch));self.assertFalse(m.run(ending))
        m.switches[242]=True;self.assertFalse(m.run(ending))
        m.switches[242]=False;m.switches[243]=True;self.assertFalse(m.run(ending))
        m.switches[242]=True;m.events.clear()
        self.assertTrue(m.run(ending));self.assertEqual(m.events,[('victory',)])
        self.assertEqual(m.clock_ms,0)

    def test_unrelated_triggers_and_every_trigger_owner_are_preserved(self):
        for mission,changed in ((206,{1,2,4,5,7}),(407,set(range(8,28)))):
            source,output,_,p=fixture(mission);before=b.triggers(source);after=b.triggers(output)
            for i,t in enumerate(before):
                with self.subTest(mission=mission,trigger=i):
                    actual=after[p['original_trigger_indices'][i]]
                    self.assertEqual(actual[2372:2400],t[2372:2400])
                    if i not in changed:self.assertEqual(actual,t)

    def test_all_other_missions_are_untouched_by_objective_correction(self):
        count=0
        for spec in b.roster_specs():
            if spec['mission_id'] in (206,407):continue
            path=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path']
            raw=path.read_bytes();chk=b.CHK(raw);row=b.metadata(spec,chk,path)
            self.assertIsNone(campaign_objectives.apply(chk,row))
            self.assertEqual(chk.save(),raw);count+=1
        self.assertEqual(count,61)


if __name__=='__main__':unittest.main()
