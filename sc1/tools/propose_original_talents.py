"""Read-only workshop snapshot and proposed implementable T01 effect bindings."""
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
def p(table,ids,field,op,value):return {'table':table,'ids':ids,'field':field,'op':op,'value':value}
def u(ids,field,op,value):return p('units',ids,field,op,value)
def w(ids,field,op,value):return p('weapons',ids,field,op,value)
ROWS=[
('b0b87a48-4e2f-4d83-b1e9-d31ab203442a',[w([0],'maxRange','add',32),u([0],'seekRange','add',1)]),
('9da04c9f-9ddd-4e51-8333-e40eb7fafd1a',[u([0],'maxHp','add',2560)]),
('11add15f-8880-4db0-9697-91723ffdfd57',[w([0],'cooldown','ratio',[100,130])]),
('b4a56885-dcef-4fd7-9b1d-1d07fa0cbd5c',[u([32],'maxHp','set',25600)]),
('3de768b5-3b1c-4aa2-a80f-fa72d5e37a73',[u([1],'maxHp','add',7680)]),
('61ca33c4-6b46-45fd-bf48-36e92fc30067',[w([2],'damageType','set',3)]),
('bec5aa24-1479-4c55-9de9-ddb843ddc039',[w([4],'cooldown','ratio',[4,5])]),
('e52e8e8a-090c-48dd-80d2-03142775c1d4',[u([2],'mineralCost','set',50),u([2],'supplyUsed','set',2),u([2],'maxHp','set',12800)]),
('8b6431dd-5553-4743-a43f-ef61172b46f6',[w([11],'maxRange','add',32),u([5,6],'seekRange','add',1)]),
('fde47c79-594b-4731-9669-0df4044da1f4',[w([27],'maxRange','add',64),u([30,31],'seekRange','add',2)]),
('911cc0df-8191-49ff-a058-8390ce15e910',[u([3],'maxHp','add',5120)]),
('adcf3a4f-948d-4c2e-b184-e48544c7afcf',[w([15,16],'maxRange','add',64),u([8],'seekRange','add',2)]),
('61c98944-9414-47f2-bcdf-6d4ff0ba5598',[u([8],'maxHp','add',7680)]),
('31e8e8c8-347d-456b-bd0d-cae47f591eb8',[w([103],'cooldown','ratio',[4,5])]),
('e4565c77-cc6f-43ea-91ee-1448e52cc757',[w([19,20],'maxRange','add',64),u([12],'seekRange','add',2)]),
('676ab7d6-96fb-5748-8796-d8570dc554e6',[u([7],'timeCost','ratio',[1,2])]),
('7bd974f2-42ce-5442-b22f-6e82fcb8fe51',[u([7],'maxHp','add',5120)]),
]
CURSES=[
('481876a7-e041-567c-91c0-dbbe5915acaf',{'type':'wave_count','numerator_per_stack':1,'denominator':4}),
('639d3bf8-b455-5b0d-9954-7695a39eb0e5',{'type':'enemy_damage','units':[37,38],'weapons':[35,38],'basis_points_per_stack':750,'rounding':'ceil once after combined stack multiplier'}),
('8704b857-aed8-5888-aac3-bada4065990d',{'type':'enemy_hp','units':[37,38],'basis_points_per_stack':1000,'rounding':'nearest1/256HP'}),
]
def main():
    board=json.load(urllib.request.urlopen('http://localhost:5173/api/board'))
    byid={x['id']:x for x in board['items']}
    proposal={'schema_version':1,'catalog_version':1,'source_board_revision':board['revision'],
      'talents':[{'id':uid,'bit_index':i,'name':byid[uid]['name'],'effect':{'type':'stat_patches','patches':patches}}
                 for i,(uid,patches) in enumerate(ROWS)],
      'curses':[{'id':uid,'byte_index':i,'name':byid[uid]['name'],'effect':effect}
                 for i,(uid,effect) in enumerate(CURSES)],
      'notes':['maxHp values use1/256HP; ranges use pixels(32=1tile); supplyUsed uses half-supply(2=1displayed).',
               'ratio patches round once to nearest integer frame, with minimum1.',
               'Existing unit HP ratio and regular Vulture used-supply difference adjusted once.',
               'T01 only: regular Terran and enemy Zerg types disjoint; Raynor type19/weapon5 excluded.',
               'Enemy damage uses original damage times(1+0.075*stacks), ceil once;5->6 and10->11 at1stack.',
               'Wave fractional quarter-unit remainder carried separately by unit type; skipped waves do not queue whole units.']}
    for filename,value in ((f'runtime_board_{board["revision"]}.json',board),('runtime_effect_proposal.json',proposal)):
        path=ROOT/'campaign'/filename
        data=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
        if filename.startswith('runtime_board_') and path.exists():assert path.read_text(encoding='utf-8')==data
        else:path.write_text(data,encoding='utf-8')
    print(json.dumps({'board_revision':board['revision'],'talents':len(ROWS),'curses':len(CURSES),'proposal':'sc1/campaign/runtime_effect_proposal.json'}))
if __name__=='__main__':main()
