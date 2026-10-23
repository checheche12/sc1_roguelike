"""Build map-specific v5 additional-wave timing and conservative hero guards.

Only original CHK files are read. No workshop, player database, installed map or
original trigger is changed. Hero types mentioned by ANY original trigger or
placed in the scenario exclude that roster, including other-owner references.
"""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sc1.native_campaign.build_all_campaigns import CHK,triggers,conditions,actions,units,unit_info

HEROES={38:[20],39:[23,25],40:[77],41:[55],42:[22],43:[79],44:[28,29],45:[51,53],46:[75],47:[79,75],48:[80,56],49:[23,25,48,78]}
HQ={106,131,132,133,154}
DEFENSE={103,406,508,606}
WORKERS={7,41,64}
# Playable infrastructure only; exclude start locations, mineral fields,
# monuments, Cerebrates and objective buildings from the opening strength.
BUILDINGS=HQ|{107,108,109,110,111,112,113,114,115,116,117,118,120,122,123,124,125,
    134,135,136,137,138,139,140,141,142,143,144,145,146,149,150,
    155,156,157,159,160,162,163,164,165,166,167,169,170,171,172}
LATE_SUPPORT={109,110,209,210,309,310,609,610}

def opening_seconds(headquarters,buildings,workers):
    """Equal infrastructure/economy weight, in fifteen-second steps."""
    # Each extra HQ counts like three support buildings. Cap both components
    # independently so a large base cannot hide a shortage of workers.
    base_steps=min(3,max(0,(max(0,headquarters-1)*3+max(0,buildings-headquarters))//3))
    worker_steps=min(3,max(0,(workers-6)//2))
    return 270-15*(base_steps+worker_steps)

def starting_strength(placed,row):
    owned=[p for p in placed if p[3]==row['owner']]
    # BW Zerg6's outlying Hatcheries are scripted sacrifices. Count only the
    # playable main island, matching the existing starting-support guard.
    if row['mission_id']==606:
        owned=[p for p in owned if (p[0]-4160)**2+(p[1]-1424)**2<=768**2]
    headquarters=sum(p[2] in HQ for p in owned)
    buildings=sum(p[2] in BUILDINGS for p in owned)
    placed_workers=sum(p[2] in WORKERS for p in owned)
    # The reviewed Zerg01 map pass adds eight Drones before play begins.
    map_workers=8 if row['mission_id']==201 else 0
    support_workers=0 if row['no_production'] else 6 if row['mission_id'] in LATE_SUPPORT else 4
    return dict(headquarters=headquarters,buildings=buildings,placed_workers=placed_workers,
        map_added_workers=map_workers,support_workers=support_workers,
        effective_workers=placed_workers+map_workers+support_workers,
        scope='main_island_only' if row['mission_id']==606 else 'initial_owned_playable_assets')

def derive():
    rows=json.loads((ROOT/'sc1/campaign/missions.json').read_text(encoding='utf8'))['missions']
    profiles=[]
    for row in rows:
        raw=Path(row['source']).read_bytes();chk=CHK(raw)
        placed=[unit_info(u) for u in units(chk)]
        own_hq=any(uid in HQ and owner==row['owner'] for _,_,uid,owner in placed)
        strength=starting_strength(placed,row)
        references={uid for _,_,uid,_ in placed if uid in {u for ids in HEROES.values() for u in ids}}
        evidence=[]
        for ti,t in enumerate(triggers(chk)):
            for ci,c in conditions(t):
                if c[15]:
                    uid=struct.unpack_from('<H',c,12)[0]
                    if uid in {u for ids in HEROES.values() for u in ids}: references.add(uid);evidence.append({'trigger':ti,'condition':ci,'type':c[15],'unit':uid})
            for ai,a in actions(t):
                if a[26]:
                    uid=struct.unpack_from('<H',a,24)[0]
                    if uid in {u for ids in HEROES.values() for u in ids}: references.add(uid);evidence.append({'trigger':ti,'action':ai,'type':a[26],'unit':uid})
        blocked=[slot for slot,ids in HEROES.items() if references.intersection(ids)]
        # New/rescued-base missions first depart no earlier than5min40sec.
        # Retain the economy-acquisition grace if the player settles later.
        first=360 if row['no_production'] else opening_seconds(strength['headquarters'],strength['buildings'],strength['effective_workers']) if own_hq else 340
        mode='disabled' if row['no_production'] else 'defense' if row['mission_id'] in DEFENSE else 'starting_base' if own_hq else 'build_or_rescue_base'
        profiles.append(dict(mission_id=row['mission_id'],label=row['label'],enabled=not row['no_production'],mode=mode,
          starting_headquarters=own_hq,starting_strength=strength,normal_first_seconds=first,normal_interval_seconds=120,
          new_base_grace_seconds=60 if row['mission_id']==101 else 240 if not own_hq else 180,
          rare_unlock_seconds=600 if row['mission_id'] in DEFENSE else 540 if not own_hq else 480,
          epic_unlock_seconds=720 if row['mission_id'] in DEFENSE else 660 if not own_hq else 600,
          legendary_unlock_seconds=840 if row['mission_id'] in DEFENSE else 780 if not own_hq else 720,
          new_base_rare_grace_seconds=360,new_base_epic_grace_seconds=480,new_base_legendary_grace_seconds=600,
          warning_seconds=20,appearance_seconds=4,blocked_hero_curse_slots=blocked,
          hero_referenced_types=sorted(references),hero_trigger_references=evidence,
          original_chk_sha256=hashlib.sha256(raw).hexdigest(),original_triggers_changed=False))
        if row['mission_id']==404:
            # The latest settling grace is5min40sec after a working economy.
            profiles[-1].update(normal_first_seconds=340,normal_interval_seconds=120,
                new_base_grace_seconds=340)
    return profiles

def build(*,write_coverage=True):
    rows=derive()
    record={'schema_version':5,'source':'original CHK metadata + latest user timing overrides','profile_count':len(rows),
      'policy':'No-production disables every added wave and timer. With an initial HQ, first departure180..270sec by starting playable buildings/HQs and workers including map/support additions; equal capped components in15sec steps. Without an initial HQ, minimum340sec with readiness-relative grace; Uraj also uses340sec after its economy becomes usable. Then120sec interval. Enemy upgrades/technology shift by the actual opening departure minus the240sec reference. Initial state is fixed; later base/worker loss never reschedules waves.',
      'cutscene_guard':'Simulation-frame clock and modal guard; scripted original assault guard uses nearby unmarked hostile combatants.',
      'hero_guard':'Conservative exclusion on any placed or original trigger-referenced hero type, independent of owner. Original hero DAT/triggers remain untouched.',
      'profiles':rows}
    out=ROOT/'sc1/native_campaign/rework_wave_profiles.json';out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    lines=['#pragma once','#include "rework_wave_policy.h"','namespace sc1_native { namespace rework_wave {','inline constexpr Profile kProfiles[]={']
    for r in rows:
        mask=sum(1<<(s-24) for s in r['blocked_hero_curse_slots'])
        vals=[r['mission_id'],str(r['enabled']).lower(),str(r['starting_headquarters']).lower(),r['normal_first_seconds'],r['normal_interval_seconds'],r['new_base_grace_seconds'],r['rare_unlock_seconds'],r['epic_unlock_seconds'],r['legendary_unlock_seconds'],r['new_base_rare_grace_seconds'],r['new_base_epic_grace_seconds'],r['new_base_legendary_grace_seconds'],mask]
        lines.append('    {'+','.join(map(str,vals))+'},')
    lines+=['};','inline const Profile* profile(std::uint32_t id) noexcept {for(const auto& p:kProfiles)if(p.mission==id)return &p;return nullptr;}','} }']
    (ROOT/'sc1/native_campaign/plugin/include/rework_wave_profiles.generated.h').write_text('\n'.join(lines)+'\n',encoding='utf8')
    if not write_coverage:return record
    contract=json.loads((ROOT/'sc1/campaign/runtime_v5_contract.json').read_text(encoding='utf8'))
    curse_rows=contract['new_curses']
    coverage={'schema_version':5,'status':'native_adapters_written_host_validation_pending','implemented_ids':[],
      'items':{},'scope':'Native added waves only. No-production missions have zero added waves; entries describe compatible production missions for choice filtering. Runtime additionally requires current anti-air/detection and a safe compatible origin.'}
    for c in curse_rows:
        slot=c.get('byte_index',c.get('index'));uid=c.get('source_id',c.get('id'))
        if slot is None:raise ValueError(('missing index',c))
        compatible=[r['mission_id'] for r in rows if r['enabled'] and slot not in r['blocked_hero_curse_slots']]
        coverage['items'][uid]={'missions':compatible,'native_slot':slot,'adapter':'include/rework_wave_native.h','original_trigger_types_preserved':True}
    verified=ROOT/'analysis/runtime_rework_20261016/wave_native_verification.json'
    if verified.is_file():
        proof=json.loads(verified.read_text(encoding='utf8'));pins=proof.get('source_hashes',{})
        adapters=['sc1/native_campaign/plugin/include/'+name for name in ('rework_curse_decl.h','rework_wave_policy.h','rework_wave_profiles.generated.h','rework_wave_native.h')]
        if all(pins.get(p)==hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in adapters):
            coverage['implemented_ids']=list(coverage['items']);coverage['status']='native_adapters_host_verified_live_pending';coverage['verification']='analysis/runtime_rework_20261016/wave_native_verification.json'
    (ROOT/'analysis/runtime_rework_20261016/wave_curse_coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return record

if __name__=='__main__':
    r=build();print(json.dumps({'profiles':r['profile_count'],'no_production':sum(not p['enabled'] for p in r['profiles']),'hero_exclusions':sum(len(p['blocked_hero_curse_slots']) for p in r['profiles'])}))
