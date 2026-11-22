# Netherlands region

An extra "area" for the start menu: the whole of the Netherlands as it was in 1839 (the year the
Amsterdam - Haarlem line opened), money in guilders (`f`). It is **not** part of the original
Railroad Tycoon; it is generated from open geodata and ships with this repository:

| File | What |
|------|------|
| `data/NETHERLANDS.png` | 256x192 map, one pixel per tile, exact EGA colours (same 16 terrain codes as the original `.PIC` maps) |
| `data/CITIES4.DTA` | 112 places in the original record format (x, y+8, 16-byte name), sorted by population |
| `data/NETHERLANDS_MENU.png` | 92x62 thumbnail for the "Select area" menu |

The game loads them like the other regions (`Region.Netherlands`, index 4 selects `CITIES4.DTA`).
Gameplay tables (cargo, industries) are the English ones: beer, livestock, textiles, steel, chemicals,
coal. The locomotives are a Dutch list (`Train_engine.nl_engines`): the English engines first, because
the first Dutch locomotives (De Arend, 1839) were British, then the continental engines of the Europe
area from 1905 on. At the 1839 start the 2-2-0 Planet and 2-2-2 De Arend are available.

Competitors are Dutch too (`Opponent.nl_leaders`): Koning Willem I and II, Thorbecke, Caland, Lely, Stork,
Regout, Philips, Heineken, Deterding, Plesman and Fokker, drawn on the portraits of the original game.

## The 1839 map

`history.py` undoes everything that is younger than the first railway: no Zuiderzee works (the
Afsluitdijk, Wieringermeer, Noordoostpolder and Flevoland are sea; Urk and Marken stay islands), no
Deltawerken (Zeeland is a set of islands, reached by ferry), the Haarlemmermeer still a lake, no
Maasvlakte or Nieuwe Waterweg (the Maas reaches the sea at Brielle), and none of the later canals
(Noordzeekanaal, Amsterdam-Rijnkanaal, Twentekanaal, Albertkanaal ...). Places that did not exist yet
(Almere, Lelystad, Emmeloord, Dronten, Hoofddorp, Nieuw-Vennep, IJmuiden) are left out, and the ports
are the ones that existed in 1839. `build_map.py --modern` produces today's country instead.

## Scale and window

One tile is 1.7 km. The map covers lon 2.15..8.53, lat 50.68..53.62 (see `geo.py`): the Netherlands in
the middle, plus the Flemish coast, the Ruhr area and the Eifel/Sauerland edge so the border regions
are not empty. Rivers are one tile wide (bridges work on them); lakes and sea need a ferry.

## Places

All Dutch places with at least 30 000 inhabitants today (Wageningen, ~35k, is the size reference): 98
Dutch places, plus 14 big places across the border (`FOREIGN` in `cities.py`; set `INCLUDE_FOREIGN =
False` to drop them). Districts of big cities (Amsterdam-Zuidoost, Leidsche Rijn ...) are skipped.
Places closer than 3 tiles are pushed apart so their villages do not merge into one blob.
Because the list is sorted by population, `Mapgen.add_city_list` uses the list index as a size
rank: Amsterdam and Rotterdam grow bigger than Meppel.

## Regenerate

```bash
tools/netherlands/fetch_geodata.sh          # once, ~25 MB into geodata/ (needs curl, unzip)
python3 tools/netherlands/build_map.py      # writes data/NETHERLANDS*.png and data/CITIES4.DTA
python3 tools/netherlands/check_data.py     # sanity checks
```

Needs Python 3 with `numpy`, `scipy` and `Pillow`.

What `build_map.py` does:

1. OSM coastline -> watertight barrier at 4x supersampling; each enclosed region is classified as sea
   or land with the OSM rule "land on the left" (so dammed bays such as the Oosterschelde work).
2. OSM lake polygons (IJsselmeer, Markermeer, Grevelingen ...) added as water.
3. Tiles are water when more than 55% (lakes: 40%) of their area is water.
4. 1839: the Zuiderzee, the Haarlemmermeer and the Maasvlakte area are painted as water; nothing is
   turned back into land (no dams). With `--modern` the OSM dams are turned back into land instead.
5. Terrain: relief from Terrarium elevation tiles (foothills > 90 m, hills > 220 m, mountains > 420 m);
   woods, heath and peat bogs from hand-drawn regions (`WOOD_AREAS`, `SWAMPS`) with noise;
   farmland patches.
6. OSM rivers as one-tile lines (minus the later canals); harbors on the sea tile nearest to 16 ports.
7. Cities: GeoNames, project, push apart, snap to dry land, write the DTA.

Resources (coal in Limburg/Aachen/Ruhr, salt in Twente/Groningen/Harlingen) are placed at game start
by `Mapgen.add_resources_list` in the rectangles given there (tile coordinates, `geo.py` converts).

## Developer shortcuts

```bash
dune exec rails -- --region 4        # skip intro and menu, start straight in the Netherlands
RAILS_SKIP_NEWS=1 dune exec rails -- --region 4   # also skip the opening newspaper popups
dune exec ./src/dump_map.exe -- 4 12345 out.png   # headless: finished map for seed 12345
```

If GL symbols are not found when running headless or in tests, run with
`LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libGL.so.1`.

## Start menu board

The wall board in the start menu has room for four lines. `Resources.extend_menu_board` makes it ten
pixels taller at the top (at runtime, from the player's own `DIFFS.PIC`) and `Start_menu` moves its text
up by the same amount, so the fifth area fits.

## Data credits

* Map data (c) OpenStreetMap contributors, ODbL 1.0, https://www.openstreetmap.org/copyright
* Place names, coordinates and populations: GeoNames, CC-BY 4.0, https://www.geonames.org/
* Elevation: Terrarium tiles from AWS Open Data (SRTM, EU-DEM and others)
