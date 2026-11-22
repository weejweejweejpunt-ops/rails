"""Decoder for Railroad Tycoon (1990) .PIC files and CITIES*.DTA lists.

Ported from bluddy/rails src/engine/utils/{pic,lzw}.ml so we can inspect the
original maps with Python. Reads only; never modifies the original files.
"""
import struct
import numpy as np

EGA = [0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,
       0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF]
EGA_RGB = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in EGA], dtype=np.uint8)


class _Bits:
    def __init__(self, data, pos):
        self.d, self.p = data, pos
        self.buf = 0
        self.nbits = 0

    def get(self, n):
        while self.nbits < n:
            self.buf |= self.d[self.p] << self.nbits
            self.p += 1
            self.nbits += 8
        v = self.buf & ((1 << n) - 1)
        self.buf >>= n
        self.nbits -= n
        return v


def _lzw(data, pos, max_bits=11):
    br = _Bits(data, pos)
    d = {i: bytes([i]) for i in range(256)}
    w = d[br.get(9)]
    out = bytearray(w)
    count, bits = 257, 9
    try:
        while True:
            k = br.get(bits)
            if k in d:
                entry = d[k]
            elif k == count:
                entry = w + w[:1]
            else:
                raise ValueError("bad code %d" % k)
            d[count] = w + entry[:1]
            out += entry
            if count + 2 > (1 << bits):
                bits += 1
            if bits > max_bits:
                d = {i: bytes([i]) for i in range(256)}
                count, bits = 256, 9
            else:
                count += 1
            w = entry
    except (IndexError, ValueError):
        pass
    return bytes(out)


def _rle(data):
    out = bytearray()
    rle, last = False, 0
    for b in data:
        if not rle and b == 0x90:
            rle = True
        elif rle and b == 0:
            out.append(0x90); last = 0x90; rle = False
        elif rle:
            out += bytes([last]) * (b - 1); rle = False
        else:
            out.append(b); last = b
    return bytes(out)


def read_pic(path):
    """Returns (h, w) uint8 array of 0..15 palette indices."""
    data = open(path, 'rb').read()
    flag, w, h = struct.unpack_from('<HHH', data, 0)
    pos = 6
    if flag & 0x8:
        pos += 16
    elif flag & 0x10:
        pos += 128
    pos += 1  # max lzw byte
    raw = _rle(_lzw(data, pos))
    stride = (w + 1) // 2
    arr = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        row = raw[y * stride:(y + 1) * stride]
        for x in range(w):
            c = row[x // 2]
            arr[y, x] = (c & 0xF) if x % 2 == 0 else (c >> 4)
    return arr


def read_cities(path):
    """CITIESn.DTA: 100 records of x(u16), y(u16, +8 menu offset), name[16]."""
    data = open(path, 'rb').read()
    out = []
    for i in range(100):
        x, y = struct.unpack_from('<HH', data, i * 20)
        name = data[i * 20 + 4:i * 20 + 20].split(b'\0')[0].decode('latin-1')
        out.append((name, x, y - 8))
    return out


def to_rgb(arr, scale=1):
    img = EGA_RGB[arr]
    if scale > 1:
        img = np.kron(img, np.ones((scale, scale, 1), dtype=np.uint8))
    return img
