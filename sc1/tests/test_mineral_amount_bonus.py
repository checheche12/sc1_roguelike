import struct
import unittest
from sc1.native_campaign import mineral_amount_bonus as bonus
from sc1.native_campaign.build_all_campaigns import CHK,assert_original_units_preserved

class MineralAmountTests(unittest.TestCase):
    def make(self,kind,stored,valid):
        row=bytearray(36);struct.pack_into('<H',row,8,kind)
        struct.pack_into('<H',row,14,valid);struct.pack_into('<I',row,20,stored)
        return CHK(b'UNIT'+struct.pack('<I',36)+row)

    def test_explicit_default_zero_and_all_types(self):
        for kind in (176,177,178):
            for stored,valid,expected in ((1500,16,2000),(0,16,500),(5432,0,2000),(65035,16,65535)):
                chk=self.make(kind,stored,valid);before=chk.getsection('UNIT')
                report=bonus.apply(chk);after=chk.getsection('UNIT')
                self.assertEqual(report['count'],1);self.assertEqual(struct.unpack_from('<I',after,20)[0],expected)
                assert_original_units_preserved(before,after,mineral_bonus=500)
                with self.assertRaises(AssertionError):assert_original_units_preserved(before,after)

    def test_gas_and_other_units_exact(self):
        for kind in (188,110,149,157,0,106):
            chk=self.make(kind,8766,16);before=chk.save();self.assertEqual(bonus.apply(chk)['count'],0);self.assertEqual(chk.save(),before)

    def test_native_overflow_and_arbitrary_edits_rejected(self):
        with self.assertRaises(ValueError):bonus.apply(self.make(176,65036,16))
        chk=self.make(176,1500,16);before=chk.getsection('UNIT');bonus.apply(chk);after=bytearray(chk.getsection('UNIT'));after[16]=1
        with self.assertRaises(AssertionError):assert_original_units_preserved(before,bytes(after),mineral_bonus=500)
