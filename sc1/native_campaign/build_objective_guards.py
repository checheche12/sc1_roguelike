"""Derive initial ordinary mission units that must be excluded from death bombs."""
import hashlib,json
from pathlib import Path
from sc1.native_campaign.build_all_campaigns import CHK,triggers,actions,conditions,cf,trigger_has_player,players_for,units,unit_info
from sc1.campaign.build_runtime_catalog import REGULAR_COMBAT_UNITS
ROOT=Path(__file__).resolve().parents[2]

def derive():
    rows=json.loads((ROOT/'sc1/campaign/missions.json').read_text(encoding='utf8'))['missions']
    guards=[];sources=[]
    for row in rows:
        raw=Path(row['source']).read_bytes();chk=CHK(raw)
        sources.append({'mission_id':row['mission_id'],'sha256':hashlib.sha256(raw).hexdigest()})
        for index,t in enumerate(triggers(chk)):
            if not any(a[26]==2 for _,a in actions(t)) or not trigger_has_player(chk,t,row['owner']):continue
            specific=[cf(c) for _,c in conditions(t) if cf(c)['type'] in (2,3,15) and cf(c)['unit'] in REGULAR_COMBAT_UNITS]
            # A named survival requirement is different from losing the entire
            # army or failing a production quota (T01/EXPZerg01).
            if len(specific)!=1:continue
            c=specific[0]
            if c['type']!=2 or c['comparison'] not in (1,10) or c['amount']!=0:continue
            # Rescue/Give scripts can change the mission units' starting owner
            # (EXPZerg08's two Dark Templars). Guard their placed identities.
            placed=[unit_info(u) for u in units(chk) if unit_info(u)[2]==c['unit']]
            if not 0<len(placed)<=8:continue
            for x,y,uid,owner in placed:
                record={'mission_id':row['mission_id'],'unit_id':uid,'owner':owner,'x':x,'y':y}
                if record not in guards:guards.append(record)
    return guards,sources

def build():
    guards,sources=derive()
    lines=['#pragma once','// Derived from original mission Defeat requirements, not ordinary army-loss conditions.',
           'namespace objective_guards {','struct Origin { U32 mission_id,unit_id,owner,x,y; };','inline constexpr Origin origins[] = {']
    for r in guards:lines.append('    {'+','.join(str(r[k]) for k in ('mission_id','unit_id','owner','x','y'))+'},')
    lines+=['};','}']
    header=ROOT/'sc1/native_campaign/plugin/include/objective_guards.generated.h'
    header.write_text('\n'.join(lines)+'\n',encoding='utf8')
    evidence=ROOT/'sc1/native_campaign/objective_guards_evidence.json'
    evidence.write_text(json.dumps({'guarded_initial_units':guards,'original_maps_checked':sources,
        'header_sha256':hashlib.sha256(header.read_bytes()).hexdigest(),'scope':'Death-bomb exclusion only; ownership transfers and transforms retain identity; reused native slots do not.'},indent=2)+'\n',encoding='utf8')
    return guards

if __name__=='__main__':print(json.dumps(build()))
