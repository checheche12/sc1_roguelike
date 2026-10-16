"""Independent format/legacy/original-requirements oracles; no game or DB I/O."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "sc1/native_campaign"
spec = importlib.util.spec_from_file_location("managed_dat_builder",HERE/"build_managed_dat.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def parse_dat(data):
    magic,major,minor,count,fields = struct.unpack_from("<IHHII",data)
    if magic != 0x2b746144 or major != 1 or count not in (228,130):
        raise ValueError("header")
    result = {}
    spans = []
    for i in range(fields):
        field,flags,offset,size = struct.unpack_from("<HHII",data,16+12*i)
        if field in result or flags > 2 or offset < 16+fields*12 or offset+size > len(data):
            raise ValueError("descriptor")
        if any(offset < end and offset+size > start for start,end in spans):
            raise ValueError("overlap")
        spans.append((offset,offset+size))
        result[field]=(flags,data[offset:offset+size])
    return count,result


def official_legacy_schema(name):
    # Deliberately independent from the builder width/subset declarations:
    # interpret the pinned maintainer's C# declarations as the oracle.
    text=(HERE/"dat_sources/tatti3/GameData/LegacyDatDecl.cs").read_text(encoding="utf-8")
    block=text.split(f"{name.title()} = new LegacyDatDecl",1)[1].split("fields = new Field[] {",1)[1].split("RefFields",1)[0]
    parts=re.split(r"// 0x[0-9a-fA-F]{2}[^\n]*\n",block)[1:]
    count={"units":228,"weapons":130}[name]
    out=[]
    for p in parts:
        scalar=re.search(r"Uint(8|16|32)\(\)",p)
        if scalar:
            width=int(scalar[1])//8
            out.append((width,0,count,bytes(width),width))
            continue
        m=re.search(r"Make(?:SubIndex)?Field\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(.*?),\s*DatFieldFormat.Uint(8|16|32)",p,re.S)
        if not m:
            raise AssertionError(p)
        width,start,length=map(int,m.group(1,2,3))
        default=(228).to_bytes(width,"little") if m[4]=="unitNone" else bytes(width)
        out.append((width,start,length,default,int(m[5])//8))
    return out


class ManagedDatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets={name:(HERE/f"managed_dat/arr/{name}.dat").read_bytes() for name in ("units","weapons")}

    def test_every_legacy_field_entry_component_and_subset_default(self):
        for name,data in self.assets.items():
            count,fields=parse_dat(data)
            raw=(ROOT/f"sc1/campaign_sources/raw/arr/{name}.dat").read_bytes()
            schema=official_legacy_schema(name)
            self.assertEqual(len(schema),54 if name=="units" else 24)
            pos=0
            for field,(width,start,length,default,scalar_width) in enumerate(schema):
                flags,body=fields[field]
                self.assertEqual(1<<flags,scalar_width)
                self.assertEqual(len(body),count*width)
                original=raw[pos:pos+length*width]
                pos+=length*width
                if name=="units" and field==43:
                    self.assertEqual(original,b"\xff\xff"*228)
                    continue
                for unit in range(count):
                    expected=original[(unit-start)*width:(unit-start+1)*width] if start<=unit<start+length else default
                    self.assertEqual(body[unit*width:(unit+1)*width],expected,(name,field,unit))
            self.assertEqual(pos,len(raw))
            self.assertEqual(set(fields),set(range(len(schema)))|({64} if name=="units" else set()))

    def test_requirements_from_independent_firegraft_decode(self):
        _,fields=parse_dat(self.assets['units'])
        offsets=struct.unpack('<228H',fields[43][1]);buffer=struct.unpack('<'+'H'*(len(fields[64][1])//2),fields[64][1])
        raw=(HERE/'dat_sources/tatti3/Resources/firegraft.fgp').read_bytes()
        pos=0
        while raw[pos:pos+4]!=b'UntR':pos+=8+struct.unpack_from('<I',raw,pos+4)[0]
        length,=struct.unpack_from('<I',raw,pos+4);section=raw[pos+8:pos+8+length]
        entries,=struct.unpack_from('<H',section);pos=2;expected={}
        for _ in range(entries):
            uid,n=section[pos:pos+2];ops=struct.unpack_from('<'+'H'*n,section,pos+2)
            if section[pos+2+n*2]:expected[uid]=ops if ops[-1]==65535 else ops+(65535,)
            pos+=3+n*2
        self.assertEqual(pos,len(section));self.assertEqual(len(expected),91)
        for uid,index in enumerate(offsets):
            if uid not in expected:self.assertEqual(index,0,uid)
            else:
                self.assertGreater(index,0);self.assertLess(index,len(buffer));self.assertEqual(buffer[index-1],uid)
                self.assertEqual(tuple(buffer[index:index+len(expected[uid])]),expected[uid],uid)
        oracle=json.loads((HERE/'dat_sources/stock_requirements_oracle.json').read_text())
        self.assertTrue(oracle['exact_contiguous_match'])
        self.assertEqual(hashlib.sha256(fields[64][1]).hexdigest(),oracle['requirements_sha256'])
        # Explicit stock tech-tree anchors: Marine->Barracks; Barracks->SCV+CC.
        self.assertEqual(expected[0],(0xff02,111,0xff08,0xff05,0xffff))
        self.assertEqual(expected[111],(0xff02,7,0xff0b,106,0xffff))

    def test_reproducible_encoding_and_source_pins(self):
        offsets,req,_=builder.original_requirements()
        for name,expected in self.assets.items():
            fields=builder.legacy_fields(name,builder.source_bytes(name))
            if name=='units':fields[43]=(1,offsets);fields[64]=(1,req)
            self.assertEqual(builder.encode(builder.SOURCES[name][0],fields),expected)
        receipt=json.loads((HERE/'managed_dat/managed_dat_evidence.json').read_text())
        for source in receipt['sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        for asset in receipt['managed_dat_assets']:
            self.assertEqual(hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest(),asset['sha256'])
        self.assertTrue(receipt['stock_values_preserved']);self.assertTrue(receipt['requirements_preserved'])
        self.assertFalse(receipt['reserved_editor_entries_added'])

    def test_reject_corrupt_descriptors(self):
        original=self.assets['weapons']
        for offset,value,fmt in [(0,0,'I'),(4,2,'H'),(16+12,0,'H'),(16+4,0,'I'),(16+8,0xffffffff,'I')]:
            bad=bytearray(original);struct.pack_into('<'+fmt,bad,offset,value)
            with self.assertRaises(ValueError):parse_dat(bad)

    def test_reject_changed_source_length(self):
        with self.assertRaises(ValueError):builder.legacy_fields('units',bytes(19875))


if __name__=='__main__':unittest.main()
