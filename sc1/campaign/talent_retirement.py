"""QA39 removed legends keep their IDs for ownership and frozen history."""
REVISION=2026102041
ORDINALS=frozenset((51,66,95,183,187,188,189,192,193,195,196))
NONCOMBAT_FAMILIES=frozenset((7,34,11,40,41,42,50,64,69,84))
NONCOMBAT_TRAIT_FAMILIES=frozenset((7,34,11,41,42,64,69,84))
def decorate(catalog):
 for item in catalog['talents']:
  spec=item.get('effect',{}).get('unit_growth',{})
  if (spec.get('kind')=='attack' and spec['units'][0] in (7,41,64)
      or spec.get('kind')=='health' and spec['units'][0] in (11,42,69)):
   item['effect'].update(offer_retired=True,unit_manual_removed=True)
  if spec.get('kind')=='trait' and item['rarity']=='epic' and spec['units'][0] in NONCOMBAT_TRAIT_FAMILIES:
   item['effect'].update(offer_retired=True,unit_trait_removed=True)
  if item.get('rework_revision')!=5 or item.get('effect_ordinal') not in ORDINALS:continue
  item['description']='삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.'
  item['effect'].update(qa_revision=REVISION,retired=True,runtime_disabled=True)
  for field in ('armor_mark_frames','marked_armor','include_armor_upgrades','include_shield_armor'):item['effect'].pop(field,None)
 catalog['talent_retirement_revision']=REVISION
 catalog['unit_growth_summary'].update(health_manuals=41,attack_manuals=31,new_unit_traits=42)
 return catalog
