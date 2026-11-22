#!/usr/bin/env python3
"""Sanity checks for the generated Netherlands data (run after build_map.py).

  python3 tools/netherlands/check_data.py [data_dir]

Exits non-zero if something is wrong, so it can be used in CI.
"""
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "data")

EGA = [0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,
       0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF]
OCEAN, HARBOR, RIVER = 1, 4, 9
MUST_HAVE = ["Amsterdam", "Rotterdam", "Den Haag", "Utrecht", "Haarlem", "Delft", "Hengelo",
             "Wageningen", "Eindhoven", "Groningen", "Maastricht", "Enschede", "Zwolle", "Leeuwarden"]

errors = []


def fail(msg):
    errors.append(msg)
    print("FAIL:", msg)


img = np.array(Image.open(os.path.join(DATA, "NETHERLANDS.png")).convert("RGB"))
if img.shape != (192, 256, 3):
    fail("map must be 256x192, got %s" % (img.shape,))
palette = {((c >> 16) & 255, (c >> 8) & 255, c & 255): i for i, c in enumerate(EGA)}
pix = np.zeros(img.shape[:2], dtype=int)
for y in range(img.shape[0]):
    for x in range(img.shape[1]):
        key = tuple(int(v) for v in img[y, x])
        if key not in palette:
            fail("pixel (%d,%d) has a non-EGA colour %s" % (x, y, key))
            break
        pix[y, x] = palette[key]

raw = open(os.path.join(DATA, "CITIES4.DTA"), "rb").read()
if len(raw) % 20:
    fail("CITIES4.DTA size %d is not a multiple of 20" % len(raw))
cities = []
for i in range(len(raw) // 20):
    x, y = struct.unpack_from("<HH", raw, i * 20)
    name = raw[i * 20 + 4:i * 20 + 20].split(b"\0")[0].decode("latin-1")
    cities.append((name, x, y - 8))

names = [c[0] for c in cities]
for want in MUST_HAVE:
    if want not in names:
        fail("missing city: " + want)
if len(set(names)) != len(names):
    fail("duplicate city names: %s" % sorted({n for n in names if names.count(n) > 1}))
for name, x, y in cities:
    if len(name) > 15:
        fail("%s: name longer than 15 characters" % name)
    if not (0 <= x < 256 and 0 <= y < 192):
        fail("%s: outside the map at (%d,%d)" % (name, x, y))
    elif pix[y, x] in (OCEAN, HARBOR, RIVER):
        fail("%s: placed on water at (%d,%d)" % (name, x, y))
close = []
for i, (a, ax, ay) in enumerate(cities):
    for b, bx, by in cities[i + 1:]:
        d = math.hypot(ax - bx, ay - by)
        if d < 2.5:
            close.append((a, b, round(d, 1)))
if close:
    fail("cities closer than 2.5 tiles: %s" % close)

print("%d cities, map %dx%d, ocean %.0f%%" % (len(cities), img.shape[1], img.shape[0], 100 * (pix == OCEAN).mean()))
sys.exit(1 if errors else 0)
