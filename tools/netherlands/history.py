"""The Netherlands as it was in 1839, the year the first railway (Amsterdam - Haarlem) opened.

The OSM data in geodata/ describes today's country.  These tables undo the big changes:

* the Zuiderzee: no Afsluitdijk, Wieringermeer, Noordoostpolder, Flevoland, Markermeer, IJsselmeer
* the Deltawerken: no Haringvlietdam, Brouwersdam, Oosterscheldekering ... (Zeeland is a set of islands)
* the Haarlemmermeer was still a lake (drained 1849-1852)
* no Maasvlakte / Europoort, and no Nieuwe Waterweg (1872): the Maas reached the sea at Brielle
* no Noordzeekanaal (1876), Amsterdam-Rijnkanaal, Twentekanaal, Albertkanaal and other later canals

All coordinates are (lon, lat).  Polygons only need to be right to within a tile (1.7 km).
"""

# The Zuiderzee as sea.  On the west and south shore the vertices lie slightly inside today's lake
# (the old shore is still the shore there); along the polders they follow the old coast.
ZUIDERZEE = [
    (5.045, 52.940),                       # Den Oever
    (4.99, 52.905), (4.935, 52.865), (4.925, 52.79), (5.00, 52.745),   # Wieringermeer inlet
    (5.11, 52.76), (5.20, 52.745), (5.285, 52.71),                       # Medemblik, Enkhuizen
    (5.21, 52.675), (5.09, 52.64), (5.06, 52.56), (5.065, 52.50),        # Hoorn, Edam, Volendam
    (5.06, 52.455), (5.02, 52.40), (5.08, 52.34), (5.17, 52.30),         # Monnickendam, Muiden, Naarden
    (5.25, 52.295), (5.35, 52.26), (5.45, 52.245),                       # Huizen, Spakenburg, Eem
    (5.57, 52.27), (5.63, 52.345), (5.76, 52.42), (5.84, 52.46),         # Putten, Harderwijk, Elburg
    (5.92, 52.52), (5.93, 52.565), (6.04, 52.625), (5.97, 52.685),       # Kampen, Genemuiden, Vollenhove
    (5.95, 52.735), (5.87, 52.79), (5.71, 52.845),                       # Blokzijl, Lemmer
    (5.55, 52.86), (5.36, 52.885), (5.35, 52.93), (5.40, 53.04),         # Stavoren, Makkum
    (5.35, 53.11), (5.05, 52.975),                                       # mouth of the Zuiderzee
]
# Islands in the Zuiderzee that survive as tiles: (name, lon, lat)
ZUIDERZEE_ISLANDS = [("Urk", 5.60, 52.66), ("Marken", 5.105, 52.46)]

HAARLEMMERMEER = [(4.62, 52.375), (4.73, 52.365), (4.765, 52.31), (4.75, 52.25), (4.68, 52.22),
                  (4.58, 52.24), (4.55, 52.30), (4.57, 52.35)]

# Land that did not exist yet: turned back into sea.
RECLAIMED_SEA = {
    "Maasvlakte": [(3.75, 52.00), (4.045, 52.00), (4.045, 51.885), (3.75, 51.885)],
}

# OSM waterway names that are younger than 1839 (the Nieuwe Merwede, Bergsche Maas and
# Nieuwe Waterweg are dug channels; the rest are canals).
LATER_WATERWAYS = {
    "Nieuwe Waterweg", "Noordzeekanaal", "Noord-Zeekanaal", "Amsterdam-Rijnkanaal", "Twentekanaal",
    "Julianakanaal", "Wilhelminakanaal", "Maas-Waalkanaal", "Merwedekanaal", "Prinses Margrietkanaal",
    "Van Starkenborghkanaal", "Eemskanaal", "Dortmund-Ems-Kanal", "Rhein-Herne-Kanal", "Albertkanaal",
    "Leopoldkanaal", "Ringvaart", "Nieuwe Merwede", "Bergsche Maas",
}
# Rivers that have since been replaced by the channels above.
OLD_RIVERS = {
    # the Maas reached the sea through the Brielse Maas, north of Voorne
    "Brielse Maas": [(4.25, 51.925), (4.19, 51.915), (4.15, 51.905), (4.10, 51.915), (4.045, 51.93)],
}

# Places that did not exist in 1839: inside the Zuiderzee or the Haarlemmermeer lake, or founded later.
GONE_PLACES = {"Almere Stad", "Lelystad", "Emmeloord", "Dronten", "Hoofddorp", "Nieuw-Vennep",
               "IJmuiden"}  # IJmuiden grew around the harbour built in 1876

# Ports that existed in 1839 (a harbor tile goes on the sea tile nearest to each point).
PORTS = [
    ("Rotterdam (Brielle)", 4.02, 51.92), ("Den Helder", 4.76, 52.97), ("Vlissingen", 3.57, 51.45),
    ("Terneuzen", 3.83, 51.33), ("Delfzijl", 6.93, 53.33), ("Harlingen", 5.41, 53.18),
    ("Oostende", 2.92, 51.23), ("Emden", 7.18, 53.35), ("Antwerpen", 4.33, 51.30),
    ("Amsterdam", 4.99, 52.40), ("Hoorn", 5.08, 52.65), ("Enkhuizen", 5.29, 52.71),
    ("Kampen", 5.93, 52.57), ("Zierikzee", 3.92, 51.65), ("Veere", 3.66, 51.55),
    ("Dunkirk", 2.37, 51.05),
]
