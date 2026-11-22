#!/usr/bin/env python3
"""Build the Netherlands region for the Rails remake of Railroad Tycoon.

Produces
  NETHERLANDS.png   256x192 map, one RGB pixel per tile, exact EGA palette colours
  CITIES4.DTA       city list in the original Railroad Tycoon record format
  NETHERLANDS_MENU.png  92x62 thumbnail for the "select area" start menu
  preview PNGs (optional, for checking the result)

Data sources (downloaded once into geodata/, see README.md):
  * OpenStreetMap (ODbL): coastline, lakes, rivers via the Overpass API
  * Terrarium elevation tiles (AWS Open Data, derived from SRTM & friends)
  * GeoNames cities15000 (CC-BY 4.0)
"""
import argparse
import json
import math
import os
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import cities as citymod
import history
from geo import *

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEO = os.environ.get("NL_GEODATA", os.path.join(REPO, "geodata"))
K = 4  # supersampling for the water mask

EGA = [0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,
       0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF]
EGA_RGB = np.array([[(c >> 16) & 255, (c >> 8) & 255, c & 255] for c in EGA], dtype=np.uint8)


# --------------------------------------------------------------------------- helpers
def load_json(name):
    with open(os.path.join(GEO, "osm", name)) as f:
        return json.load(f)


def sub_xy(lon, lat):
    x, y = to_tile(lon, lat)
    return x * K, y * K


def stitch(ways):
    """Join OSM way geometries (lists of (lon,lat)) into closed rings."""
    ways = [list(w) for w in ways if len(w) > 1]
    rings = []
    while ways:
        ring = ways.pop()
        grew = True
        while grew and ring[0] != ring[-1]:
            grew = False
            for i, w in enumerate(ways):
                if w[0] == ring[-1]:
                    ring += w[1:]
                elif w[-1] == ring[-1]:
                    ring += w[::-1][1:]
                elif w[-1] == ring[0]:
                    ring = w[:-1] + ring
                elif w[0] == ring[0]:
                    ring = w[::-1][:-1] + ring
                else:
                    continue
                ways.pop(i)
                grew = True
                break
        if ring[0] == ring[-1] and len(ring) > 3:
            rings.append(ring)
    return rings


def geom_of(el):
    return [(p["lon"], p["lat"]) for p in el["geometry"]]


# --------------------------------------------------------------------------- water
def sea_mask():
    """Boolean (H*K, W*K) mask of salt water.

    The coastline ways are drawn as a watertight barrier; the image is split into
    connected regions, and every region is classified with the OSM rule that land
    lies on the left and water on the right of a coastline way.  This also finds
    bays that are cut off from the open sea by a dam (Oosterschelde, Grevelingen...).
    """
    img = Image.new("L", (MAP_W * K, MAP_H * K), 0)
    d = ImageDraw.Draw(img)
    ways = [[sub_xy(*p) for p in geom_of(el)] for el in load_json("coastline.json")["elements"]]
    for pts in ways:
        d.line(pts, fill=255, width=1)
    barrier = np.array(img) > 0
    labels, n = ndimage.label(~barrier)  # 4-connected: 8-connected lines are watertight
    right = np.zeros(n + 1)
    left = np.zeros(n + 1)
    H, W = labels.shape

    for pts in ways:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length < 1.5:
                continue
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            nx, ny = -dy / length, dx / length          # right-hand normal, image coords (y down)
            for sign, store in ((1, right), (-1, left)):
                for dist in (2.0, 3.0, 4.0):
                    px, py = int(mx + sign * nx * dist), int(my + sign * ny * dist)
                    if 0 <= px < W and 0 <= py < H and labels[py, px] > 0:
                        store[labels[py, px]] += 1
                        break
    sea_labels = np.where(right > left)[0]
    sea_labels = sea_labels[sea_labels > 0]
    return np.isin(labels, sea_labels)


def lake_mask():
    img = Image.new("L", (MAP_W * K, MAP_H * K), 0)
    d = ImageDraw.Draw(img)
    for el in load_json("lakes.json")["elements"] + load_json("water2.json")["elements"]:
        if el["type"] == "relation":
            outer = [geom_of(m) for m in el["members"] if m.get("role") == "outer" and "geometry" in m]
            inner = [geom_of(m) for m in el["members"] if m.get("role") == "inner" and "geometry" in m]
            for ring in stitch(outer):
                d.polygon([sub_xy(*p) for p in ring], fill=255)
            for ring in stitch(inner):
                d.polygon([sub_xy(*p) for p in ring], fill=0)
        elif el["type"] == "way":
            g = geom_of(el)
            if len(g) > 3 and g[0] == g[-1]:
                d.polygon([sub_xy(*p) for p in g], fill=255)
    return np.array(img) > 0


def downsample_frac(mask):
    h, w = mask.shape
    return mask.reshape(h // K, K, w // K, K).mean(axis=(1, 3))


# --------------------------------------------------------------------------- elevation
def elevation():
    """Mean terrain height (m) per tile from Terrarium tiles (z=8)."""
    Z = 8
    tiles = {}
    for fn in os.listdir(os.path.join(GEO, "terrarium")):
        _, tx, ty = fn[:-4].split("_")
        a = np.array(Image.open(os.path.join(GEO, "terrarium", fn)).convert("RGB"), dtype=np.float64)
        tiles[(int(tx), int(ty))] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    xs = [t[0] for t in tiles]
    ys = [t[1] for t in tiles]
    x0, y0 = min(xs), min(ys)
    mosaic = np.zeros(((max(ys) - y0 + 1) * 256, (max(xs) - x0 + 1) * 256))
    for (tx, ty), a in tiles.items():
        mosaic[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a
    n = 2 ** Z * 256
    # sample at the centre of every sub-sample (K*K per tile) and average
    gx, gy = np.meshgrid((np.arange(MAP_W * 2) + 0.5) / 2, (np.arange(MAP_H * 2) + 0.5) / 2)
    lon, lat = to_lonlat(gx, gy)
    px = (lon + 180) / 360 * n - x0 * 256
    py = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n - y0 * 256
    px = np.clip(px.astype(int), 0, mosaic.shape[1] - 1)
    py = np.clip(py.astype(int), 0, mosaic.shape[0] - 1)
    h = mosaic[py, px]
    return h.reshape(MAP_H, 2, MAP_W, 2).mean(axis=(1, 3))


# --------------------------------------------------------------------------- drawing
def bresenham(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def polyline_tiles(lonlats):
    pts = [to_tile(lon, lat) for lon, lat in lonlats]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        yield from bresenham(ax, ay, bx, by)


def poly_mask(polys):
    img = Image.new("L", (MAP_W, MAP_H), 0)
    d = ImageDraw.Draw(img)
    for p in polys:
        d.polygon([to_tile(*pt) for pt in p], fill=255)
    return np.array(img) > 0


def smooth_noise(seed, sigma):
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal((MAP_H, MAP_W)), sigma, mode="wrap")
    return (n - n.mean()) / n.std()


# --------------------------------------------------------------------------- hand-drawn regions (lon, lat)
WOOD_AREAS = {
    "Veluwe": [(5.65, 52.34), (5.85, 52.36), (6.00, 52.33), (6.08, 52.20), (6.10, 52.08), (6.00, 52.00),
               (5.90, 51.99), (5.72, 52.02), (5.60, 52.07), (5.58, 52.20), (5.58, 52.30)],
    "Utrechtse Heuvelrug": [(5.20, 52.12), (5.38, 52.12), (5.47, 52.05), (5.46, 51.99), (5.35, 51.99), (5.25, 52.04)],
    "Sallandse Heuvelrug": [(6.34, 52.40), (6.52, 52.40), (6.52, 52.27), (6.40, 52.25)],
    "Montferland": [(6.05, 51.90), (6.17, 51.96), (6.17, 51.87)],
    "Reichswald": [(5.95, 51.72), (6.20, 51.80), (6.20, 51.68), (5.97, 51.66)],
    "Maasduinen": [(6.05, 51.57), (6.18, 51.62), (6.20, 51.42), (6.08, 51.38)],
    "Brabantse Kempen": [(5.05, 51.60), (5.40, 51.64), (5.62, 51.58), (5.64, 51.38), (5.40, 51.30), (5.15, 51.33), (5.08, 51.46)],
    "Belgische Kempen": [(5.00, 51.34), (5.60, 51.36), (5.62, 51.05), (5.20, 51.05), (4.95, 51.20)],
    "Dwingelderveld": [(6.30, 52.88), (6.45, 52.86), (6.46, 52.78), (6.32, 52.78)],
    "Drents-Friese Wold": [(6.12, 53.02), (6.35, 53.03), (6.35, 52.92), (6.15, 52.92)],
    "Kennemerduinen": [(4.52, 52.45), (4.60, 52.45), (4.58, 52.30), (4.50, 52.30)],
    "Schoorlse duinen": [(4.62, 52.72), (4.69, 52.72), (4.67, 52.62), (4.60, 52.62)],
    "Hoge Veluwe-zoom Nijmegen": [(5.85, 51.84), (5.97, 51.86), (5.97, 51.77), (5.85, 51.78)],
    "Hamerkwartier Twente": [(6.80, 52.35), (7.00, 52.33), (7.02, 52.20), (6.82, 52.20)],
    "Ruhr-Hohe Mark": [(6.90, 51.80), (7.20, 51.82), (7.20, 51.66), (6.92, 51.65)],
    "Sonsbeck-Xanten": [(6.40, 51.68), (6.60, 51.68), (6.62, 51.58), (6.40, 51.58)],
}
SWAMPS = {
    "De Peel": [(5.75, 51.50), (5.98, 51.50), (6.00, 51.30), (5.80, 51.30)],
    "Biesbosch": [(4.65, 51.78), (4.88, 51.78), (4.90, 51.70), (4.68, 51.68)],
    "Weerribben-Wieden": [(5.90, 52.80), (6.15, 52.80), (6.15, 52.62), (5.92, 52.62)],
    "Fochteloerveen": [(6.30, 53.08), (6.45, 53.08), (6.45, 52.98), (6.30, 52.98)],
    "Bargerveen": [(6.95, 52.74), (7.10, 52.74), (7.10, 52.62), (6.95, 52.62)],
    "Oostvaardersplassen": [(5.30, 52.46), (5.45, 52.46), (5.45, 52.38), (5.30, 52.38)],
    "Groene Hart": [(4.65, 52.14), (4.92, 52.12), (4.92, 52.00), (4.66, 52.00)],
    "Zuidlaardermeer": [(6.60, 53.15), (6.75, 53.15), (6.75, 53.05), (6.60, 53.05)],
    "Land van Saeftinghe": [(4.05, 51.38), (4.25, 51.37), (4.25, 51.31), (4.05, 51.31)],
}

# Dams and causeways that OSM does not name consistently: lon/lat polylines that turn
# water tiles into land.  Most other dams come from geodata/osm/dams.json.
EXTRA_DAMS = {
    "Houtribdijk": [(5.296, 52.703), (5.36, 52.62), (5.44, 52.525)],
    "Zandkreekdam": [(3.845, 51.553), (3.865, 51.535)],
    "Veerse Gatdam": [(3.70, 51.568), (3.72, 51.555)],
    "Lauwersmeerdijk": [(6.19, 53.38), (6.20, 53.35)],
}

# Ports: a Harbor tile is placed on the sea tile nearest to each of these points.
PORTS = [
    ("Hoek van Holland", 4.10, 51.98), ("IJmuiden", 4.55, 52.465), ("Den Helder", 4.76, 52.97),
    ("Vlissingen", 3.57, 51.45), ("Terneuzen", 3.83, 51.33), ("Delfzijl", 6.93, 53.33),
    ("Harlingen", 5.41, 53.18), ("Zeebrugge", 3.20, 51.34), ("Oostende", 2.92, 51.23),
    ("Eemshaven", 6.83, 53.45), ("Emden", 7.18, 53.35), ("Antwerpen", 4.33, 51.30),
    ("Amsterdam", 4.95, 52.40), ("Dunkirk", 2.37, 51.05),
]


# --------------------------------------------------------------------------- main build
def build(args):
    sea = sea_mask()
    lakes = lake_mask()
    water = (downsample_frac(sea) >= args.water_threshold) | (downsample_frac(lakes) >= args.lake_threshold)

    elev = elevation()
    land = ~water

    dam = np.zeros((MAP_H, MAP_W), dtype=bool)
    if args.modern:
        # --- dams turn water into land
        dam_lines = [geom_of(el) for el in load_json("dams.json")["elements"] if "geometry" in el]
        dam_lines += list(EXTRA_DAMS.values())
        for line in dam_lines:
            for x, y in polyline_tiles(line):
                if 0 <= x < MAP_W and 0 <= y < MAP_H:
                    dam[y, x] = True
        water &= ~dam
    else:
        # --- 1839: no dams, Zuiderzee instead of IJsselmeer/polders, Haarlemmermeer still a lake
        water |= poly_mask([history.ZUIDERZEE])
        water |= poly_mask([history.HAARLEMMERMEER])
        water |= poly_mask(history.RECLAIMED_SEA.values())
        for _, lon, lat in history.ZUIDERZEE_ISLANDS:
            x, y = (int(v) for v in to_tile(lon, lat))
            water[y, x] = False
    land = ~water

    # --- base terrain
    pix = np.full((MAP_H, MAP_W), CLEAR, dtype=np.uint8)
    pix[water] = OCEAN

    # farmland: clustered patches on low, non-urban land
    farm_noise = smooth_noise(7, 2.2)
    pix[land & (farm_noise > 0.35)] = FARM

    # woods: hand-drawn regions (patchy), plus high ground
    wood_poly = poly_mask(WOOD_AREAS.values())
    wood_noise = smooth_noise(11, 1.6)
    wood_soft = ndimage.gaussian_filter(wood_poly.astype(float), 1.0)
    in_wood = land & (wood_soft > 0.5) & (wood_noise > -0.45)
    high = land & (elev >= 110)
    pix[in_wood] = WOODS
    pix[high & (smooth_noise(13, 1.2) > -0.3)] = WOODS

    swamp_poly = poly_mask(SWAMPS.values())
    swamp_soft = ndimage.gaussian_filter(swamp_poly.astype(float), 1.3) + 0.25 * smooth_noise(17, 1.0)
    pix[land & (swamp_soft > 0.5)] = SWAMP

    # relief: foothills / hills / mountains from the elevation model
    pix[land & (elev >= 90) & (pix != WOODS) & (pix != SWAMP)] = FOOTHILLS
    pix[land & (elev >= 220)] = HILLS
    pix[land & (elev >= 420)] = MOUNTAIN

    # --- rivers (only on land tiles)
    river = np.zeros((MAP_H, MAP_W), dtype=bool)
    for el in load_json("rivers.json")["elements"]:
        if "geometry" not in el:
            continue
        if not args.modern and el.get("tags", {}).get("name") in history.LATER_WATERWAYS:
            continue
        for x, y in polyline_tiles(geom_of(el)):
            if 0 <= x < MAP_W and 0 <= y < MAP_H:
                river[y, x] = True
    if not args.modern:
        for line in history.OLD_RIVERS.values():
            for x, y in polyline_tiles(line):
                if 0 <= x < MAP_W and 0 <= y < MAP_H:
                    river[y, x] = True
    pix[river & ~water] = RIVER
    pix[dam & ~water] = CLEAR
    river &= ~dam

    # --- cities
    cs = citymod.load_cities(historic=not args.modern)
    place_cities(cs, pix, water, river)
    return pix, cs, dict(elev=elev, water=water, sea=sea, lakes=lakes)



def place_cities(cs, pix, water, river, min_dist=3.0):
    """Project cities, push crowded ones apart and snap them onto dry land."""
    for c in cs:
        c["fx"], c["fy"] = to_tile(c["lon"], c["lat"])
    for _ in range(60):
        moved = False
        for i, a in enumerate(cs):
            for b in cs[i + 1:]:
                dx, dy = b["fx"] - a["fx"], b["fy"] - a["fy"]
                d = math.hypot(dx, dy)
                if d < min_dist:
                    if d < 1e-6:
                        dx, dy, d = 1.0, 0.0, 1.0
                    push = (min_dist - d)
                    wa = b["pop"] / (a["pop"] + b["pop"])   # bigger city moves less
                    a["fx"] -= dx / d * push * wa
                    a["fy"] -= dy / d * push * wa
                    b["fx"] += dx / d * push * (1 - wa)
                    b["fy"] += dy / d * push * (1 - wa)
                    moved = True
        if not moved:
            break
    for c in cs:
        x, y = int(math.floor(c["fx"])), int(math.floor(c["fy"]))
        c["ox"], c["oy"] = x, y
        # snap to nearest dry (non-water, non-river) tile
        best = None
        for r in range(0, 8):
            for yy in range(y - r, y + r + 1):
                for xx in range(x - r, x + r + 1):
                    if 0 <= xx < MAP_W and 0 <= yy < MAP_H and not water[yy, xx] and not river[yy, xx]:
                        dd = (xx - c["fx"]) ** 2 + (yy - c["fy"]) ** 2
                        if best is None or dd < best[0]:
                            best = (dd, xx, yy)
            if best:
                break
        c["x"], c["y"] = best[1], best[2]
    # snapping can bring two places back together: move the smaller one to the nearest free dry tile
    for c in sorted(cs, key=lambda c: c["pop"]):
        others = [o for o in cs if o is not c]
        if all(math.hypot(o["x"] - c["x"], o["y"] - c["y"]) >= 2.8 for o in others):
            continue
        best = None
        for yy in range(c["y"] - 5, c["y"] + 6):
            for xx in range(c["x"] - 5, c["x"] + 6):
                if not (0 <= xx < MAP_W and 0 <= yy < MAP_H) or water[yy, xx] or river[yy, xx]:
                    continue
                if any(math.hypot(o["x"] - xx, o["y"] - yy) < 2.8 for o in others):
                    continue
                dd = (xx - c["fx"]) ** 2 + (yy - c["fy"]) ** 2
                if best is None or dd < best[0]:
                    best = (dd, xx, yy)
        if best:
            c["x"], c["y"] = best[1], best[2]


def add_ports(pix, ports):
    placed = []
    for name, lon, lat in ports:
        fx, fy = to_tile(lon, lat)
        best = None
        for yy in range(max(0, int(fy) - 7), min(MAP_H, int(fy) + 8)):
            for xx in range(max(0, int(fx) - 7), min(MAP_W, int(fx) + 8)):
                if pix[yy, xx] != OCEAN:
                    continue
                coastal = any(
                    0 <= xx + dx < MAP_W and 0 <= yy + dy < MAP_H and
                    pix[yy + dy, xx + dx] not in (OCEAN, HARBOR, RIVER)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not coastal:
                    continue
                dd = (xx - fx) ** 2 + (yy - fy) ** 2
                if best is None or dd < best[0]:
                    best = (dd, xx, yy)
        if best:
            pix[best[2], best[1]] = HARBOR
            placed.append((name, best[1], best[2]))
    return placed


# --------------------------------------------------------------------------- outputs
def write_dta(cs, path):
    with open(path, "wb") as f:
        for c in cs:
            name = c["name"].encode("latin-1")[:15]
            f.write(struct.pack("<HH", c["x"], c["y"] + 8) + name.ljust(16, b"\0"))


def write_map_png(pix, path):
    Image.fromarray(EGA_RGB[pix]).save(path)


def write_menu_thumb(pix, path):
    """92x62 thumbnail for the start menu: nearest-neighbour downscale of the map."""
    h, w = pix.shape
    out = np.zeros((62, 92), dtype=np.uint8)
    # only the NL part of the map is interesting: crop 160x? around the middle
    x0, x1, y0, y1 = 20, 236, 0, 192
    for y in range(62):
        for x in range(92):
            sx0 = x0 + x * (x1 - x0) / 92
            sx1 = x0 + (x + 1) * (x1 - x0) / 92
            sy0 = y0 + y * (y1 - y0) / 62
            sy1 = y0 + (y + 1) * (y1 - y0) / 62
            blk = pix[int(sy0):max(int(sy0) + 1, int(sy1)), int(sx0):max(int(sx0) + 1, int(sx1))].ravel()
            vals, counts = np.unique(blk, return_counts=True)
            out[y, x] = vals[np.argmax(counts)]
    Image.fromarray(EGA_RGB[out]).save(path)


def write_preview(pix, cs, path, scale=5, labels=True):
    img = Image.fromarray(EGA_RGB[pix]).resize((MAP_W * scale, MAP_H * scale), Image.NEAREST)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    for c in cs:
        cx, cy = c["x"] * scale + scale // 2, c["y"] * scale + scale // 2
        d.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 0, 0), outline=(255, 255, 255))
        if labels:
            d.text((cx + 5, cy - 6), c["name"], fill=(255, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "data"))
    ap.add_argument("--preview-dir", default=None)
    ap.add_argument("--water-threshold", type=float, default=0.55)
    ap.add_argument("--lake-threshold", type=float, default=0.40)
    ap.add_argument("--modern", action="store_true", help="today's coast, dams and polders instead of 1839")
    args = ap.parse_args()

    pix, cs, dbg = build(args)
    ports = add_ports(pix, PORTS if args.modern else history.PORTS)

    # drop city markers: the game itself draws cities from CITIES4.DTA
    os.makedirs(args.out, exist_ok=True)
    write_map_png(pix, os.path.join(args.out, "NETHERLANDS.png"))
    write_dta(cs, os.path.join(args.out, "CITIES4.DTA"))
    write_menu_thumb(pix, os.path.join(args.out, "NETHERLANDS_MENU.png"))
    if args.preview_dir:
        os.makedirs(args.preview_dir, exist_ok=True)
        write_preview(pix, cs, os.path.join(args.preview_dir, "nl_preview.png"))
        write_preview(pix, cs, os.path.join(args.preview_dir, "nl_plain.png"), labels=False)
        e = dbg["elev"]
        Image.fromarray(np.clip(e / 3 + 40, 0, 255).astype(np.uint8)).resize((MAP_W * 3, MAP_H * 3)).save(
            os.path.join(args.preview_dir, "nl_elev.png"))
    vals, counts = np.unique(pix, return_counts=True)
    names = "Slum Ocean Clear Woods Harbor Coal Swamp Foothills Oil River Farm Hills Village Enemy City Mountain".split()
    print("tile counts:", {names[v]: int(c) for v, c in zip(vals, counts)})
    print("harbors:", ports)
    # connectivity: which cities cannot be reached from Amsterdam without a ferry?
    ground = pix != OCEAN
    ground &= pix != HARBOR
    lab, _ = ndimage.label(ground, structure=np.ones((3, 3)))
    home = [c for c in cs if c["name"] == "Amsterdam"][0]
    ref = lab[home["y"], home["x"]]
    cut = [c["name"] for c in cs if lab[c["y"], c["x"]] != ref]
    print("not connected to Amsterdam by land (ferry needed):", cut)
    print("(in 1839 Zeeland, Walcheren, Goeree-Overflakkee etc. are islands: that is intended)" if not args.modern else "")
    print("cities:", len(cs), " window lon %.2f..%.2f lat %.2f..%.2f" % (LON0, LON1, LAT1, LAT0))
    return pix, cs


if __name__ == "__main__":
    main()
