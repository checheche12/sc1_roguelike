"""User-requested low ground south of Protoss09's lower-left settlement.

Use ordinary jungle dirt tile pairs and remove the cliff decorations within
the bounded southern hill. MTXM is the engine terrain; TILE mirrors the custom
tile edit. ISOM brush metadata and all units/triggers/resources stay intact.
"""
from __future__ import annotations
import struct
from . import mining_layout_audit as mining

MISSION=309
BOUNDS=(4,121,38,128)  # 32px tiles, right/bottom exclusive
TAGS=('MTXM','TILE','DD2 ','THG2')

def _tile_flags(tile,cv5,vf4):
    mega=struct.unpack_from('<H',cv5,(tile>>4)*52+20+(tile&15)*2)[0]
    return struct.unpack_from('<16H',vf4,mega*32)

def apply(chk,row):
    if row['mission_id']==608:return _gas_exit(chk)
    if row['mission_id']!=MISSION:return None
    width,height=struct.unpack('<HH',chk.getsection('DIM '))
    assert (width,height)==(128,128) and int.from_bytes(chk.getsection('ERA '),'little')&7==4
    cv5,vf4=mining._terrain_bytes(4)
    def flat(tile):return all((flags&7)==1 for flags in _tile_flags(tile,cv5,vf4))
    variants=[i for i in range(16) if flat(2*16+i) and flat(3*16+i)]
    assert variants
    x1,y1,x2,y2=BOUNDS;terrain=list(struct.unpack('<'+str(width*height)+'H',chk.getsection('MTXM')))
    changed=[]
    # Preserve existing low-ground jungle/dirt transitions. Replace complete
    # left/right pairs only where the old hill or its doodad blocks ground.
    for y in range(y1,y2):
        for x in range(x1,x2,2):
            if flat(terrain[y*width+x]) and flat(terrain[y*width+x+1]):continue
            variant=variants[(x//2*5+y*3)%len(variants)]
            for xx,group in ((x,2),(x+1,3)):
                new=group*16+variant;assert flat(new)
                at=y*width+xx;old=terrain[at];terrain[at]=new
                changed.append(dict(x=xx,y=y,before=old,after=new))
    if changed:
        chk.setsection('MTXM',struct.pack('<'+str(len(terrain))+'H',*terrain))
        if b'TILE' in chk.sections:
            editor=bytearray(chk.getsection('TILE'));assert len(editor)==width*height*2
            for change in changed:struct.pack_into('<H',editor,(change['y']*width+change['x'])*2,change['after'])
            chk.setsection('TILE',bytes(editor))
    removed={}
    for tag,stride in (('DD2 ',8),('THG2',10)):
        if tag.encode() not in chk.sections:continue
        raw=chk.getsection(tag);assert len(raw)%stride==0;keep=[];entries=[]
        for at in range(0,len(raw),stride):
            record=raw[at:at+stride];_,x,y=struct.unpack_from('<HHH',record)
            if x1*32<=x<x2*32 and y1*32<=y<y2*32:entries.append(record.hex())
            else:keep.append(record)
        chk.setsection(tag,b''.join(keep));removed[tag]=entries
    assert all(flat(terrain[y*width+x]) for y in range(y1,y2) for x in range(x1,x2))
    return dict(revision=1,mission=MISSION,bounds_tiles=list(BOUNDS),changed_tiles=changed,removed_decorations=removed,all_patch_tiles_walkable_low_ground=True,units_and_resources_unchanged=True,isometric_brush_metadata_preserved=True,actual_gameplay_verified=False)

def _gas_exit(chk):
    """Open the trapped south exit of EXPZerg08's right-hand main geyser."""
    width,height=struct.unpack('<HH',chk.getsection('DIM '))
    assert (width,height)==(192,96) and int.from_bytes(chk.getsection('ERA '),'little')&7==3
    cv5,vf4=mining._terrain_bytes(3)
    flat=lambda tile:all((flags&7)==1 for flags in _tile_flags(tile,cv5,vf4))
    variants=[i for i in range(16) if flat(32+i) and flat(48+i)]
    terrain=bytearray(chk.getsection('MTXM'));changed=[]
    # A 64x64 opening joins the pocket to the base below the mineral line.
    # Keep every resource, unit, trigger and the rest of the hill in place.
    for y in range(71,73):
        variant=variants[(22*5+y*3)%len(variants)]
        for x,group in ((44,2),(45,3)):
            at=(y*width+x)*2;old=struct.unpack_from('<H',terrain,at)[0];new=group*16+variant
            if old!=new:
                struct.pack_into('<H',terrain,at,new);changed.append(dict(x=x,y=y,before=old,after=new))
    chk.setsection('MTXM',bytes(terrain))
    if b'TILE' in chk.sections:
        editor=bytearray(chk.getsection('TILE'));assert len(editor)==width*height*2
        for change in changed:struct.pack_into('<H',editor,(change['y']*width+change['x'])*2,change['after'])
        chk.setsection('TILE',bytes(editor))
    return dict(revision=1,mission=608,bounds_tiles=[44,71,46,73],changed_tiles=changed,
        removed_decorations={},all_patch_tiles_walkable_low_ground=True,units_and_resources_unchanged=True,
        isometric_brush_metadata_preserved=True,actual_gameplay_verified=False)

def verify(source_chk,output_chk,row,report):
    from .build_all_campaigns import CHK
    expected=CHK(source_chk.save());actual=apply(expected,row)
    if actual!=report:raise ValueError('Settlement terrain receipt differs from the bounded edit')
    for tag in TAGS:
        if expected.sections.get(tag.encode())!=output_chk.sections.get(tag.encode()):raise ValueError('Unauthorized terrain/decorations edit: '+tag)
    return actual
