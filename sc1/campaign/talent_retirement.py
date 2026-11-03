"""Removed talents keep their IDs for ownership and frozen history."""
REVISION=2026102041
UNIT_CLEANUP_REVISION=2026110302
# Keep wire fields and frozen ownership; remove these cards from live rewards.
UNIT_CLEANUP_ORDINALS=frozenset((164,173,210,211,245,246,264,265,283,303,314))
ORDINALS=frozenset((51,60,66,75,85,95,183,187,188,189,192,193,195,196))
NONCOMBAT_FAMILIES=frozenset((7,34,11,40,41,42,50,64,69,84))
NONCOMBAT_TRAIT_FAMILIES=frozenset((7,34,11,41,42,64,69,84))
def unit_cleanup_retired(item):
 return item.get('rework_revision')==5 and item.get('effect_ordinal') in UNIT_CLEANUP_ORDINALS

def decorate(catalog):
 for item in catalog['talents']:
  if unit_cleanup_retired(item):
   item['description']='삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.'
   item['effect'].update(qa_revision=UNIT_CLEANUP_REVISION,retired=True,runtime_disabled=True,offer_retired=True)
  spec=item.get('effect',{}).get('unit_growth',{})
  if (spec.get('kind')=='attack' and spec['units'][0] in (7,41,64)
      or spec.get('kind')=='health' and spec['units'][0] in (11,42,69)):
   item['effect'].update(offer_retired=True,unit_manual_removed=True)
  if spec.get('kind')=='trait' and item['rarity']=='epic' and spec['units'][0] in NONCOMBAT_TRAIT_FAMILIES:
   item['effect'].update(offer_retired=True,unit_trait_removed=True)
  if item.get('rework_revision')!=5 or item.get('effect_ordinal') not in ORDINALS:continue
  item['description']='삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.'
  revision={60:2026102488,75:2026102493,85:2026102371}.get(item['effect_ordinal'],REVISION)
  item['effect'].update(qa_revision=revision,retired=True,runtime_disabled=True)
  if item['effect_ordinal'] in (60,75,85):item['effect'].update(offer_retired=True)
  if item['effect_ordinal']==75:
   for field in tuple(item['effect']):
    if field.startswith('creep_'):item['effect'].pop(field)
  for field in ('armor_mark_frames','marked_armor','include_armor_upgrades','include_shield_armor'):item['effect'].pop(field,None)
 catalog['talent_retirement_revision']=UNIT_CLEANUP_REVISION
 if 'single_target_legend_ordinals' in catalog:
  catalog['single_target_legend_ordinals']=[n for n in catalog['single_target_legend_ordinals'] if n not in ORDINALS]
 catalog['unit_growth_summary'].update(health_manuals=38,attack_manuals=28,new_unit_traits=39)
 return catalog
