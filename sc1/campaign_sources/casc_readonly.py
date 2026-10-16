"""Strict read-only CascLib fork: even build/config opens request no write access."""
from pathlib import Path
import ctypes as C

ROOT = Path(__file__).resolve().parent
DLL = ROOT / 'tools/CascLib-readonly/build-ninja/CascLib.dll'
lib = C.WinDLL(str(DLL), use_last_error=True)
H = C.c_void_p
D = C.c_uint32
B = C.c_bool

def bind(name, restype, *args):
    fn = getattr(lib, name)
    fn.restype = restype
    fn.argtypes = args
    return fn

open_storage = bind('CascOpenStorage', B, C.c_wchar_p, D, C.POINTER(H))
close_storage = bind('CascCloseStorage', B, H)
open_file = bind('CascOpenFile', B, H, C.c_char_p, D, D, C.POINTER(H))
get_size = bind('CascGetFileSize64', B, H, C.POINTER(C.c_uint64))
read_file = bind('CascReadFile', B, H, C.c_void_p, D, C.POINTER(D))
close_file = bind('CascCloseFile', B, H)
get_error = bind('GetCascError', D)

class FindData(C.Structure):
    _fields_ = [('name', C.c_char * 260), ('ckey', C.c_ubyte * 16),
                ('ekey', C.c_ubyte * 16), ('tags', C.c_uint64),
                ('size', C.c_uint64), ('plain', C.c_void_p),
                ('file_id', D), ('locale', D), ('content', D),
                ('spans', D), ('available', D), ('name_type', D)]

find_first = bind('CascFindFirstFile', H, H, C.c_char_p, C.POINTER(FindData), C.c_wchar_p)
find_next = bind('CascFindNextFile', B, H, C.POINTER(FindData))
find_close = bind('CascFindClose', B, H)

def checked(ok):
    if not ok:
        raise OSError(get_error(), 'CascLib local read failed')

class Storage:
    def __init__(self, path, locale=4):
        self.handle = H()
        self.locale = locale
        checked(open_storage(str(Path(path).resolve()), locale, C.byref(self.handle)))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        checked(close_storage(self.handle))

    def read(self, name):
        h, size, count = H(), C.c_uint64(), D()
        checked(open_file(self.handle, name.replace('/', '\\').encode(), self.locale, 0x10, C.byref(h)))
        try:
            checked(get_size(h, C.byref(size)))
            if size.value > 128 * 1024 * 1024:
                raise ValueError('Asset exceeds extraction size cap')
            buf = C.create_string_buffer(size.value)
            checked(read_file(h, buf, size.value, C.byref(count)))
            assert count.value == size.value
            return buf.raw
        finally:
            checked(close_file(h))

    def find(self, mask='*'):
        data = FindData()
        h = find_first(self.handle, mask.encode(), C.byref(data), None)
        if h in (None, C.c_void_p(-1).value):
            return
        try:
            while True:
                yield {'name': data.name.decode('utf-8', 'replace'), 'bytes': data.size,
                       'available': bool(data.available & 1), 'locale': data.locale,
                       'ckey': bytes(data.ckey).hex(), 'ekey': bytes(data.ekey).hex()}
                if not find_next(h, C.byref(data)):
                    break
        finally:
            checked(find_close(h))
