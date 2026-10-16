from pathlib import Path
import struct,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'analysis/all_campaign_20261015/visual_resources/iscript.bin'
OUT=ROOT/'sc1/native_campaign/iscript_effects'
HEADER=ROOT/'sc1/native_campaign/plugin/include/movement_iscript.generated.h'
ARGS=['H','H','B','B','BB','B','BB','H','HBB','HBB','H','H','','HBB','HBB','HBB','HBB','HBB','H','HBB','HBB','HB','','B','H','var','HH','','var','','BH','B','B','','B','B','B','B','','','B','B','','B','B','','','','','B','','','B','H','','H','B','H','HH','HHH','HHH','BB','','H','H','B','HBB','','']
COUNTS={0:2,1:2,2:4,12:14,13:14,14:16,15:16,20:22,21:22,23:24,24:26,26:28,27:28,28:28,29:28}
BRANCH={7:1,30:2,53:1,57:1,58:3,59:5,60:5,63:1}
STOP={7,22,54,48} # goto, end, return, ignorerest
CUSTOM=(0xcd,0xce,0xcf)
def u16(b,p):return struct.unpack_from('<H',b,p)[0]
def parse(code):
    table=u16(code,0);headers={};fields=[];entries=[];meta=set(range(4));p=table
    while True:
        ident,off=struct.unpack_from('<HH',code,p);meta.update(range(p,p+4))
        if ident==0xffff:break
        assert ident not in headers and code[off:off+4]==b'SCPE',(ident,off)
        headers[ident]=off;fields.append(p+2)
        count=COUNTS[code[off+4]];meta.update(range(off,off+8+count*2))
        for at in range(off+8,off+8+count*2,2):
            fields.append(at)
            if u16(code,at):entries.append(u16(code,at))
        p+=4
    commands={};covered={};todo=list(entries)
    while todo:
        p=todo.pop()
        if p in commands:continue
        assert 4<=p<len(code) and p not in meta and p not in covered,('bad entry',p)
        op=code[p];assert op<len(ARGS),('bad opcode',p,op)
        fmt=ARGS[op];size=2+2*code[p+1] if fmt=='var' else 1+struct.calcsize('<'+fmt)
        assert p+size<=len(code)
        for x in range(p,p+size):
            assert x not in meta and x not in covered,('overlap',p,x)
            covered[x]=p
        commands[p]=(op,size)
        if op in BRANCH:
            target=u16(code,p+BRANCH[op]);assert target,('zero branch',p);todo.append(target)
        if op not in STOP:todo.append(p+size)
    return table,headers,fields,commands,meta

def build(code):
    table,headers,fields,commands,meta=parse(code)
    def reachable(start):
        seen=set();todo=[start]
        while todo:
            p=todo.pop()
            if not p or p in seen:continue
            seen.add(p);op,size=commands[p]
            if op in BRANCH:todo.append(u16(code,p+BRANCH[op]))
            if op not in STOP:todo.append(p+size)
        return seen
    selected=set();animation_fields=[]
    for ident,h in headers.items():
        for at in range(h+8,h+8+COUNTS[code[h+4]]*2,2):
            start=u16(code,at)
            if not start:continue
            seen=reachable(start)
            if any(commands[p][0] in (28,41) for p in seen):
                selected.update(seen);animation_fields.append(at)
    # Append closed CFG clones, preserving EVERY original command/header address.
    # Only selected animation entry pointers change. Native internal fixed script
    # positions still see the original bytes, unlike whole-file relocation.
    out=bytearray(code);entry_map={};native_map={};events=[]
    for p in sorted(selected):
        op,size=commands[p];entry_map[p]=len(out)
        if op==28:events.append({'offset':len(out),'event':0xce,'original':p});out.append(0xce)
        native_map[p]=len(out);out.extend(code[p:p+size])
        if op in (28,41):
            event=0xcd if op==41 else 0xcf
            events.append({'offset':len(out),'event':event,'original':p});out.append(event)
    assert len(out)<0x10000,('16-bit overflow',len(out))
    for at in animation_fields:struct.pack_into('<H',out,at,entry_map[u16(code,at)])
    for p in selected:
        op,size=commands[p]
        if op in BRANCH:struct.pack_into('<H',out,native_map[p]+BRANCH[op],entry_map[u16(code,p+BRANCH[op])])
    pointer_bytes={x for at in animation_fields for x in (at,at+1)}
    for p,b in enumerate(code):
        if p not in pointer_bytes:assert out[p]==b,('original byte changed',p)
    for p in selected:
        op,size=commands[p];actual=bytearray(out[native_map[p]:native_map[p]+size])
        if op in BRANCH:
            assert u16(actual,BRANCH[op])==entry_map[u16(code,p+BRANCH[op])]
            struct.pack_into('<H',actual,BRANCH[op],u16(code,p+BRANCH[op]))
        assert actual==code[p:p+size],('clone byte changed',p)
        if op==28:assert out[entry_map[p]]==0xce and out[native_map[p]+size]==0xcf
        if op==41:assert out[native_map[p]+size]==0xcd
        if op not in STOP:
            assert native_map[p]+size+(1 if op in (28,41) else 0)==entry_map[p+size],('fallthrough',p)
    return bytes(out),{'source_size':len(code),'output_size':len(out),'headers':len(headers),'native_commands':len(commands),'cloned_commands':len(selected),'selected_animations':len(animation_fields),'move_commands':sum(commands[p][0]==41 for p in selected),'melee_commands':sum(commands[p][0]==28 for p in selected),'branch_commands':sum(commands[p][0] in BRANCH for p in selected),'original_bytes_preserved_except_animation_entry_pointers':True,'all_original_code_and_header_addresses_preserved':True,'clone_native_command_equivalence':True,'fallthrough_and_all_branch_targets_verified':True,'events':events,'animation_entry_patches':[{'field':at,'before':u16(code,at),'after':u16(out,at)} for at in animation_fields]}

def main():
    original=SRC.read_bytes();output,evidence=build(original);OUT.mkdir(exist_ok=True)
    (OUT/'iscript.bin').write_bytes(output)
    evidence.update(schema=1,source=str(SRC.relative_to(ROOT)),source_sha256=hashlib.sha256(original).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),live_verified=False,game_accessed=False,sources=['https://raw.githubusercontent.com/neivv/teippi/master/src/iscript.cpp','https://raw.githubusercontent.com/neivv/aice/master/src/iscript.rs','https://raw.githubusercontent.com/neivv/aise/master/bw_dat/src/bw/structs.rs'])
    (OUT/'iscript_effects_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n','utf8')
    event_rows=','.join('{%d,%d}'%(x['offset'],x['event']) for x in evidence['events'])
    body='\n'.join('    '+','.join('0x%02x'%x for x in output[i:i+24])+',' for i in range(0,len(output),24))
    HEADER.write_text('#pragma once\n// Generated by build_effect_iscript.py; native code addresses retained; selected animation CFG clones appended.\nnamespace movement_effects::data {\ninline constexpr unsigned char kIscript[] = {\n'+body+'\n};\nstruct Event{unsigned short offset;unsigned char opcode;};\ninline constexpr Event kEvents[]={'+event_rows+'};\ninline constexpr unsigned kOriginalSize='+str(len(original))+';\ninline constexpr unsigned kMoveOpcode=0xcd,kMeleeEnterOpcode=0xce,kMeleeLeaveOpcode=0xcf;\ninline constexpr const char kOriginalSha256[]="'+evidence['source_sha256']+'";\ninline constexpr const char kPatchedSha256[]="'+evidence['output_sha256']+'";\n}\n','utf8')
    print(json.dumps({k:v for k,v in evidence.items() if k not in ('events','animation_entry_patches')},indent=2))
if __name__=='__main__':main()
