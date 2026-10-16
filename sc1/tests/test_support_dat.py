"""Independent original-schema, requirements, stock-buttons and closure oracles."""
from pathlib import Path
import hashlib
import json
import re
import struct
import unittest

from sc1.native_campaign import build_support_dat as build


def parse(raw):
    magic,major,minor,count,n=struct.unpack_from('<IHHII',raw)
    if magic!=0x2b746144 or major!=1 or minor==0 or n>1024:raise ValueError('Loader header contract')
    result={};spans=[]
    for i in range(n):
        field,flags,off,size=struct.unpack_from('<HHII',raw,16+12*i)
        if field in result or flags>2 or off<16+n*12 or off+size>len(raw):raise ValueError('Invalid descriptor')
        if any(off<end and off+size>start for start,end in spans):raise ValueError('Overlap')
        spans.append((off,off+size));result[field]=(1<<flags,raw[off:off+size])
    return count,result


def official_schema(name):
    text=(build.TATTI/'GameData/LegacyDatDecl.cs').read_text(encoding='utf-8')
    title={'techdata':'TechData','portdata':'PortData','mapdata':'MapData'}.get(name,name.title())
    block=text.split(f'{title} = new LegacyDatDecl',1)[1].split('fields = new Field[] {',1)[1].split('RefFields',1)[0]
    count={'flingy':209,'sprites':517,'images':999,'upgrades':61,'techdata':44,'portdata':110,'mapdata':65,'orders':189}[name]
    fields=[]
    for source in re.split(r'// 0x[0-9a-f]{2}[^\n]*\n',block)[1:]:
        scalar=re.search(r'Uint(8|16|32)\(\)',source)
        if scalar:fields.append((int(scalar[1])//8,0,count));continue
        sub=re.search(r'MakeField\((\d+),\s*(\d+),\s*(\d+),',source)
        if not sub:raise AssertionError(source)
        fields.append(tuple(map(int,sub.groups())))
    return count,fields


def raw_requirements(tag):
    raw=(build.TATTI/'Resources/firegraft.fgp').read_bytes();pos=0
    while raw[pos:pos+4]!=tag.encode():pos+=8+struct.unpack_from('<I',raw,pos+4)[0]
    length,=struct.unpack_from('<I',raw,pos+4);raw=raw[pos+8:pos+8+length];pos=2;result={}
    for _ in range(struct.unpack_from('<H',raw)[0]):
        uid,n=raw[pos:pos+2];ops=struct.unpack_from('<'+'H'*n,raw,pos+2)
        if raw[pos+2+n*2]:result[uid]=ops if ops[-1:]==(65535,) else ops+(65535,)
        pos+=3+n*2
    if pos!=len(raw):raise AssertionError('FGP end')
    return result


def values(body,width):
    return tuple(int.from_bytes(body[i:i+width],'little') for i in range(0,len(body),width))


def all_assets():
    return {**build.expected_assets(),**build.expected_managed_assets()}


class SupportDatTests(unittest.TestCase):
    def test_exact_loader_file_and_full_field_closure(self):
        assets=all_assets();proof=json.loads((build.PROOF/'loader_field_schema.json').read_text())
        self.assertEqual(len(assets),11);self.assertEqual(set(assets),set(build.REQUIRED_LOADER_DAT_NAMES))
        expected_counts=dict(units=261,weapons=131,flingy=209,sprites=517,images=999,upgrades=62,techdata=45,portdata=110,mapdata=65,orders=189,buttons=99)
        for name,ids in proof['complete_field_ids'].items():
            count,fields=parse(assets[f'arr/{name}.dat'])
            self.assertEqual(count,expected_counts[name]);self.assertEqual(set(fields),set(ids),name)
        self.assertEqual(proof['diagnostic_hex_proof']['digits'],'0123456789abcdef')
        self.assertEqual(proof['diagnostic_hex_proof']['formatter_rva'],'0xbd0c0')
        formatter=bytes.fromhex(proof['diagnostic_hex_proof']['formatter_bytes'])
        self.assertIn(bytes.fromhex('c0e804'),formatter);self.assertIn(bytes.fromhex('4183e10f'),formatter)
        build.validate_field_closure(assets)

    def test_all_eleven_outputs_exact_executed_pinned_writer(self):
        evidence=json.loads(build.REFERENCE_EVIDENCE.read_text())
        self.assertTrue(evidence['behavioral_sources_unmodified']);self.assertFalse(evidence['native_game_execution'])
        self.assertEqual(evidence['commit'],'eb940dab410e9e197db9634322e91fb67a0b7f0f')
        self.assertIn('roundtrip checks passed',evidence['stdout'])
        self.assertEqual(len(evidence['outputs']),11)
        for source in evidence['sources']+evidence['inputs']+evidence['outputs']:
            self.assertEqual(hashlib.sha256((build.ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        for name,raw in all_assets().items():self.assertEqual(raw,(build.REFERENCE/name).read_bytes(),name)
        for core in ('GameData.cs','DatTable.cs','LegacyDatDecl.cs','Firegraft.cs'):
            source=build.TATTI/'GameData'/core
            self.assertTrue(any(x['path']==source.relative_to(build.ROOT).as_posix() for x in evidence['sources']))

    def test_all_original_support_values_and_subset_padding(self):
        for path,asset in build.expected_assets().items():
            name=Path(path).stem
            if name=='buttons':continue
            count,fields=parse(asset);original_count,schema=official_schema(name)
            raw=(build.ROOT/f'sc1/campaign_sources/raw/arr/{name}.dat').read_bytes();pos=0
            req_fields={6} if name=='upgrades' else {4,5} if name=='techdata' else {17} if name=='orders' else set()
            for field,(width,start,length) in enumerate(schema):
                original=raw[pos:pos+width*length];pos+=width*length
                actual_width,body=fields[field];self.assertEqual(len(body),actual_width*count)
                if field in req_fields:self.assertEqual(original,b'\xff\xff'*original_count);continue
                for entry in range(original_count):
                    expected=original[(entry-start)*width:(entry-start+1)*width] if start<=entry<start+length else bytes(width)
                    self.assertEqual(int.from_bytes(body[entry*actual_width:(entry+1)*actual_width],'little'),int.from_bytes(expected,'little'),(name,field,entry))
            self.assertEqual(pos,len(raw))
        # Canonical u32 widening preserves every weapon/tech reference value.
        _,orders=parse(build.expected_assets()['arr/orders.dat'])
        self.assertEqual(orders[13][0],4);self.assertEqual(orders[14][0],4)

    def test_requirements_and_two_documented_canonical_order_migrations(self):
        oracle=json.loads((build.PROOF/'stock_requirements_oracle.json').read_text())
        for name,bindings in {'upgrades':[(6,16,'UpgR')],'techdata':[(4,16,'TecR'),(5,17,'TecU')],'orders':[(17,32,'OrdR')]}.items():
            count,fields=parse(build.expected_assets()[f'arr/{name}.dat'])
            for offset,buffer,tag in bindings:
                offsets=values(fields[offset][1],2);words=values(fields[buffer][1],2);expected=raw_requirements(tag)
                if tag=='OrdR':
                    self.assertEqual(expected[36],(65535,));self.assertEqual(expected[102],(65535,))
                    expected[36]=(0xff0c,65535);expected[102]=(0xff13,65535)
                for uid,index in enumerate(offsets):
                    if uid not in expected:self.assertEqual(index,0)
                    else:
                        self.assertGreater(index,0);self.assertEqual(words[index-1],uid)
                        self.assertEqual(words[index:index+len(expected[uid])],expected[uid],(tag,uid))
                if tag!='OrdR':self.assertEqual(hashlib.sha256(fields[buffer][1]).hexdigest(),oracle['requirements'][tag]['sha256'])
                self.assertTrue(oracle['requirements'][tag]['exact_contiguous_match'])
        spec=(build.TATTI/'datspec.md').read_text()
        self.assertIn("tatti doesn't make distinction between no reqs enabled and no reqs",spec)
        self.assertIn('Has no Addon',spec)

    def test_all_stock_buttons_and_explicit_unit_group_mapping(self):
        raw=(build.PROOF/'buttons.bin').read_bytes();sets,buttons=struct.unpack_from('<HH',raw)
        self.assertEqual((sets,buttons),(99,554));self.assertEqual(hashlib.sha256(raw).hexdigest(),build.BUTTON_SHA)
        count,fields=parse(build.expected_assets()['arr/buttons.dat']);self.assertEqual(count,sets)
        pos=754;starts=struct.unpack_from('<99H',raw,pos);pos+=198;counts=raw[pos:pos+99];pos+=198
        self.assertEqual(values(fields[0][1],4),starts);self.assertEqual(fields[1][1],counts)
        for start,n in zip(starts,counts):self.assertLessEqual(start+n,554)
        for column in range(8):
            width=1 if column==0 else 2;size=width*554
            self.assertEqual(fields[column+2],(width,raw[pos:pos+size]));pos+=size
        self.assertEqual(pos,len(raw))
        _,units=parse(build.expected_units_asset())
        maps=values(units[0x44][1],2);linked=values(units[0x45][1],2)
        self.assertEqual(maps[:250],tuple(raw[4:254]));self.assertEqual(linked[:250],struct.unpack_from('<250H',raw,254))
        self.assertEqual(maps[250:],(0,)*11);self.assertEqual(linked[250:],(65535,)*11)
        self.assertEqual(maps[229:250],(79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,16,97,98))
        self.assertTrue(all(x<99 for x in maps))

    def test_derived_managed_original_values_and_unit_requirements(self):
        for name,original_count,expected_count,expected_sha in [('units',228,261,build.BASE_UNITS_SHA),('weapons',130,131,build.BASE_WEAPONS_SHA)]:
            path=build.HERE/f'managed_dat/arr/{name}.dat';base=path.read_bytes()
            self.assertEqual(hashlib.sha256(base).hexdigest(),expected_sha)
            base_count,original=parse(base);count,fields=parse(build.expected_managed_assets()[f'arr/{name}.dat'])
            self.assertEqual(base_count,original_count);self.assertEqual(count,expected_count)
            for field,(width,body) in original.items():
                actual_width,actual=fields[field]
                if name=='units' and field==64:self.assertEqual(actual,body);continue
                subvalues=len(body)//(original_count*width)
                self.assertEqual(values(actual,actual_width)[:original_count*subvalues],values(body,width),(name,field))
            self.assertEqual(path.read_bytes(),base)
        _,units=parse(build.expected_units_asset())
        for field,default in [(1,228),(2,228),(3,228),(12,23),(13,23),(14,23),(15,23),(16,23),(17,130),(19,130),(24,1)]:
            self.assertEqual(values(units[field][1],units[field][0])[228:],(default,)*33,field)
        self.assertEqual(values(units[66][1],2),tuple(range(261)));self.assertEqual(values(units[67][1],2),tuple(range(261)))
        self.assertEqual(values(units[43][1],2)[228:],(0,)*33)

    def test_full_default_variable_lists_and_special_unit_defaults(self):
        assets=all_assets()
        for name,offset,length,data_ids,expected_items in [('units',0x4e,0x4f,[0x50,0x51,0x52],3),('upgrades',0x11,0x12,[0x13],34),('upgrades',0x14,0x15,[0x16,0x17,0x18,0x19,0x1a,0x1b],34),('techdata',0x12,0x13,[0x14],39)]:
            count,fields=parse(assets[f'arr/{name}.dat']);starts=values(fields[offset][1],fields[offset][0]);sizes=values(fields[length][1],fields[length][0])
            self.assertEqual(len(starts),count);self.assertEqual(len(sizes),count);self.assertEqual(sum(sizes),expected_items)
            for field in data_ids:self.assertEqual(len(values(fields[field][1],fields[field][0])),expected_items)
            for start,n in zip(starts,sizes):self.assertLessEqual(start+n,expected_items)
        _,u=parse(assets['arr/units.dat'])
        v=lambda f:values(u[f][1],u[f][0])
        self.assertEqual(v(0x4a)[40],1800);self.assertEqual(v(0x4c),(51200,)*261)
        self.assertEqual(v(0x53)[8],9);self.assertEqual(v(0x54)[8],65523)
        self.assertEqual(v(0x53)[1],10);self.assertEqual(v(0x54)[1],65526)
        self.assertEqual(v(0x46)[57],4102);self.assertEqual(v(0x48)[4],32)
        self.assertTrue(v(0x47)[42]&0x180);self.assertTrue(v(0x55)[125]&0x691690)

    def test_every_declared_field_missing_rejected(self):
        assets=all_assets();checks=0
        for path,raw in assets.items():
            count,fields=build.decode(raw)
            for field in fields:
                changed=dict(fields);del changed[field]
                candidate=dict(assets);candidate[path]=build.encode(count,changed)
                with self.assertRaises(ValueError,msg=(path,field)):build.validate_field_closure(candidate)
                checks+=1
        self.assertEqual(checks,204)
        old_partial=(build.HERE/'managed_dat/arr/units.dat').read_bytes();count,fields=build.decode(old_partial);fields[66]=(1,struct.pack('<228H',*range(228)))
        candidate=dict(assets);candidate['arr/units.dat']=build.encode(count,fields)
        with self.assertRaises(ValueError):build.validate_field_closure(candidate)

    def test_read_only_inputs_and_current_generated_receipt(self):
        protected=[build.HERE/'managed_dat/arr/units.dat',build.HERE/'managed_dat/arr/weapons.dat',build.HERE/'plugin/native_plugin.dll',build.HERE/'plugin/native_plugin_build_evidence.json']
        before={p:p.read_bytes() for p in protected};assets=all_assets()
        for path,raw in assets.items():
            target=build.OUT/'derived'/Path(path).name if Path(path).stem in ('units','weapons') else build.OUT/path
            self.assertEqual(target.read_bytes(),raw)
        for path,raw in before.items():self.assertEqual(path.read_bytes(),raw)
        receipt=json.loads((build.OUT/'support_dat_evidence.json').read_text())
        for item in receipt['sources']+receipt['support_dat_assets']+receipt['derived_managed_assets']:
            self.assertEqual(hashlib.sha256((build.ROOT/item['path']).read_bytes()).hexdigest(),item['sha256'],item['path'])
        for key in ('stock_values_preserved','requirements_preserved','buttons_preserved','all_eleven_outputs_exact_canonical','loader_declared_field_closure_verified'):self.assertTrue(receipt[key])
        self.assertFalse(receipt['native_play_verified']);self.assertEqual(len(receipt['canonical_order_migrations']),2)

    def test_reject_legacy_and_truncated_data(self):
        with self.assertRaises(ValueError):parse(build.source_bytes('flingy'))
        with self.assertRaises(ValueError):build.legacy_fields('flingy',build.source_bytes('flingy')[:-1])


if __name__=='__main__':unittest.main()
