"""Compile the validated expanded runtime catalog into native static arrays."""
import json
from pathlib import Path
from .runtime_catalog import load_catalog
from .build_runtime_catalog import UNIT_FIELDS, WEAPON_FIELDS, RARITY_LABELS, REGULAR_COMBAT_UNITS
ROOT=Path(__file__).resolve().parents[2]

def render(catalog=None):
    """Return the complete native contract, including current UI copy."""
    from .effect_copy import describe_effect
    catalog=catalog or load_catalog(expected_version=2)
    talents=sorted(catalog['talents'],key=lambda x:x['bit_index'])
    curses=sorted(catalog['curses'],key=lambda x:x['byte_index'])
    masks=[0]*16
    for item in talents:
        storage=item.get('wire_storage')
        if storage is None:masks[item['bit_index']//32]|=1<<(item['bit_index']%32)
        elif storage['word']<=16:masks[storage['word']-1]|=((1<<storage['width'])-1)<<storage['shift']
    lines=['#pragma once','// Generated compatibility catalog; historical indices remain unchanged.',
      '#include <cstdint>','namespace frozen {',
      f'inline constexpr std::uint32_t kCatalogVersion = {catalog["catalog_version"]};',
      f'inline constexpr std::uint32_t kTalentCount = {len(talents)};',
      f'inline constexpr std::uint32_t kCurseCount = {len(curses)};',
      'inline constexpr std::uint32_t kLegacyTalentCount = 238, kLegacyCurseCount = 15;',
      'inline constexpr std::uint32_t kRegularCombatUnits[] = {'+','.join(map(str,REGULAR_COMBAT_UNITS))+'};',
      'inline constexpr std::uint32_t kCurseMaxStacks[kCurseCount] = {'+','.join(str(x['max_stacks'])+'u' for x in curses)+'};',
      'inline constexpr std::uint32_t kTalentMasks[16] = {'+','.join(str(x)+'u' for x in masks)+'};',
      'struct Patch {std::uint32_t bit,table,field,id,op,numerator,denominator;};',
      'inline constexpr Patch patches[] = {']
    for item in talents:
        for p in item['effect'].get('patches',[]):
            table={'units':0,'weapons':1}[p['table']]
            field=(UNIT_FIELDS if table==0 else WEAPON_FIELDS)[p['field']]
            op={'set':0,'add':1,'ratio':2}[p['op']]
            n,d=p['value'] if op==2 else (p['value'],1)
            for uid in p['ids']: lines.append('    {'+','.join(map(str,(item['bit_index'],table,field,uid,op,n,d)))+'},')
    lines.extend(['};','struct Movement {std::uint32_t bit,unit_id,numerator,denominator;};','inline constexpr Movement movement_patches[] = {'])
    for item in talents:
        for p in item['effect'].get('movement',[]):
            lines.append('    {'+','.join(map(str,(item['bit_index'],p['unit_id'],p['numerator'],p['denominator'])))+'},')
    lines.extend(['};','struct MultiTarget {std::uint32_t bit,unit_id,mode,max_targets;};',
                  'inline constexpr MultiTarget multi_target_patches[] = {'])
    for item in talents:
        effect=item['effect']
        if effect.get('type')=='multi_target':
            mode={'independent_layers':0,'shared_cycle':1}[effect['mode']]
            lines.append('    {'+','.join(map(str,(item['bit_index'],effect['unit_id'],mode,effect['max_targets'])))+'},')
    lines.append('};')
    for prefix,items in (('talent',talents),('curse',curses)):
        for key,field in (('rarities','rarity'),('names','name'),('effects','description')):
            vals=[RARITY_LABELS[x[field]] if field=='rarity' else describe_effect(x) if field=='description' else x[field] for x in items]
            lines.append('inline constexpr const char* '+prefix+'_'+key+'[] = {'+', '.join(json.dumps(x,ensure_ascii=False) for x in vals)+'};')
    lines.extend(['inline constexpr int home[2] = {232,376};','inline constexpr int slots[4][2] = {{88,264},{184,264},{280,264},{376,264}};',
      'inline constexpr int center[2] = {232,312};','inline constexpr char marker[] = "SC1_NATIVE_ALL_V1_R469_C1";','}'])
    return '\n'.join(lines)+'\n'


def generate(catalog=None):
    target=ROOT/'sc1/native_campaign/plugin/include/frozen_catalog.generated.h'
    target.write_text(render(catalog),encoding='utf-8')
    return target

if __name__=='__main__':print(generate())
