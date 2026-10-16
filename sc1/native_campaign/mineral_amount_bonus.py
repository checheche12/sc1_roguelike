"""Increase each placed mineral field's effective CHK amount exactly once."""
import hashlib
import struct

BONUS = 500
MINERALS = (176, 177, 178)


def apply(chk, bonus=BONUS):
    raw = chk.getsection('UNIT')
    if len(raw) % 36:
        raise ValueError('Malformed UNIT section')
    out = bytearray(raw)
    fields = []
    for index, at in enumerate(range(0, len(raw), 36)):
        if struct.unpack_from('<H', raw, at + 8)[0] not in MINERALS:
            continue
        valid = struct.unpack_from('<H', raw, at + 14)[0]
        stored = struct.unpack_from('<I', raw, at + 20)[0]
        # Native scenario loading defaults minerals to 1500 unless the
        # resource-amount property is explicitly enabled (OpenBW bwgame).
        before = stored if valid & 0x10 else 1500
        after = before + bonus
        if not 0 <= after <= 65535:
            raise ValueError(f'Mineral amount exceeds native U16: {index}')
        struct.pack_into('<H', out, at + 14, valid | 0x10)
        struct.pack_into('<I', out, at + 20, after)
        fields.append(dict(record=index, stored_before=stored, effective_before=before,
                           after=after, valid_before=valid))
    chk.setsection('UNIT', bytes(out))
    return dict(policy='all_placed_minerals_plus_500_v1', bonus=bonus,
                count=len(fields), fields=fields,
                before_unit_sha256=hashlib.sha256(raw).hexdigest(),
                after_unit_sha256=hashlib.sha256(out).hexdigest())
