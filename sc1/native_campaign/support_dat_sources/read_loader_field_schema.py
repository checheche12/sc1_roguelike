"""Read only the exact loader's DAT schema/formatter bytes; no DLL execution."""
from pathlib import Path
import hashlib
import json
import struct

HERE=Path(__file__).resolve().parent
LOADER=Path("C:/Users/chech/AppData/Local/Temp/samase/samase_dll.dll")
EXPECTED="6b0d6c1016e637ef433f962b9c4b06c091fef81c515ec9bf747158ffab599c3c"


def run():
    raw=LOADER.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError("Exact loader changed")
    pe=struct.unpack_from('<I',raw,0x3c)[0];n=struct.unpack_from('<H',raw,pe+6)[0]
    opt=pe+24;size=struct.unpack_from('<H',raw,pe+20)[0];base=struct.unpack_from('<Q',raw,opt+24)[0]
    sections=[]
    for i in range(n):
        _,rva,length,start=struct.unpack_from('<IIII',raw,opt+size+i*40+8)
        sections.append((rva,length,start))
    def read(rva,n):
        for address,length,start in sections:
            if address<=rva and rva+n<=address+length:return raw[start+rva-address:start+rva-address+n]
        raise ValueError("RVA outside file sections")
    names=('units','weapons','flingy','upgrades','techdata','sprites','images','orders','sfxdata','portdata','mapdata','buttons')
    tables={}
    for index,name in enumerate(names):
        ptr,length=struct.unpack('<QQ',read(0x274490+index*16,16))
        widths=list(read(ptr-base,length)) if length else []
        tables[name]={"loader_index":index,"width_table_rva":hex(ptr-base) if length else None,"declared_slots":length,"runtime_widths":widths,"nonzero_field_ids":[i for i,w in enumerate(widths) if w]}
    alphabet=read(0x272600,16)
    if alphabet!=b'0123456789abcdef':raise ValueError("Unexpected integer formatter alphabet")
    req={'units':[0x40],'upgrades':[0x10],'techdata':[0x10,0x11],'orders':[0x20]}
    fields={name:sorted(set(info['nonzero_field_ids'])|set(req.get(name,[]))) for name,info in tables.items() if name!='sfxdata'}
    proof={"loader_path":str(LOADER),"loader_sha256":EXPECTED,"loader_version":"0.10.28-64","read_only_file_analysis":True,"executed":False,
        "schema_table_rva":"0x274490","schema_reference_rva":"0x15b9b5","schema_query_note":"Runtime table descriptor helper loads the width table at15b9b5, bounds-checks field slot and checks nonzero width at15b9d2. Zero-width variable requirement buffers are supplied separately from pinned source schema.",
        "tables":tables,"complete_field_ids":fields,
        "width_note":"Runtime widths include pointer conversion for images/portdata/mapdata and button-param normalization. File integer widths are canonical writer output, not blindly replaced by these runtime widths.",
        "diagnostic_hex_proof":{"error_branch_rva":"0x198c23","field_formatter_pointer_rva":"0x198c59","formatter_rva":"0xbd0c0","formatter_bytes":read(0xbd0c0,0x7c).hex(),"shift_instruction_rva":"0xbd0e7","mask_instruction_rva":"0xbd0ea","digit_table_rva":"0x272600","digits":alphabet.decode(),"conclusion":"Units41 is hexadecimal0x41 (wireframe mode), not decimal41."},
        "scope":"Completeness against every declared field slot plus canonical requirement buffers. Individual field lookups may be conditional; no claim that every field is unconditionally read at startup or that offline proof verifies native play."}
    (HERE/'loader_field_schema.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof


if __name__=='__main__':
    print(json.dumps(run(),indent=2))
