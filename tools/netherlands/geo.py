"""Shared geometry helpers for the Netherlands map generator.

The Rails/Railroad Tycoon map is a 256x192 grid of 16-colour "pixels" (tiles).
We project WGS84 longitude/latitude onto that grid with a simple, fixed
equirectangular projection (square tiles of TILE_KM kilometres).
"""
import math

MAP_W, MAP_H = 256, 192

# Window of the world covered by the map (top-left corner) and tile size.
TILE_KM = 1.70
LON0 = 2.15          # west edge
LAT0 = 53.62         # north edge
_COS_LAT = math.cos(math.radians(52.2))
TILES_PER_DEG_X = 111.32 * _COS_LAT / TILE_KM
TILES_PER_DEG_Y = 111.19 / TILE_KM

LON1 = LON0 + MAP_W / TILES_PER_DEG_X
LAT1 = LAT0 - MAP_H / TILES_PER_DEG_Y


def to_tile(lon, lat):
    """lon/lat -> fractional tile coordinates (x right, y down)."""
    return (lon - LON0) * TILES_PER_DEG_X, (LAT0 - lat) * TILES_PER_DEG_Y


def to_lonlat(x, y):
    return LON0 + x / TILES_PER_DEG_X, LAT0 - y / TILES_PER_DEG_Y


# Palette indices used by Rails' `Tilemap.pixel` enum (also the EGA colour numbers).
SLUM, OCEAN, CLEAR, WOODS, HARBOR, COAL, SWAMP, FOOTHILLS, OILWELL, RIVER, FARM, HILLS, \
    VILLAGE, ENEMY, CITY, MOUNTAIN = range(16)
