"""Select and name the places that go into the Netherlands scenario.

Source: GeoNames cities15000 (CC-BY 4.0, https://www.geonames.org/).
Every Dutch place with at least MIN_POP inhabitants is included (Wageningen,
~35k, is the "size" reference).  City districts and suburbs that GeoNames
lists as separate entries are dropped.  A handful of large places just across
the border are added so that the border regions are not empty.
"""
import csv
import os

import history

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEONAMES = os.path.join(os.environ.get("NL_GEODATA", os.path.join(REPO, "geodata")), "geonames", "extracted", "cities15000.txt")

MIN_POP = 30000
INCLUDE_FOREIGN = True

# GeoNames name -> in-game name (max 15 chars, plain ASCII like the original game)
RENAME_NL = {
    "The Hague": "Den Haag",
    "'s-Hertogenbosch": "Den Bosch",
    "Almere Stad": "Almere",
    "Alphen aan den Rijn": "Alphen a/d Rijn",
    "Capelle aan den IJssel": "Capelle a/d IJ",
    "Krimpen aan den IJssel": "Krimpen a/d IJ",
}

# GeoNames entries that are districts of other places or duplicates.
DROP_NL = {
    "Noord", "Osdorp", "Leidsche Rijn", "Hoogvliet", "Groot IJsselmonde", "Ypenburg",
    "Zaanstad",            # same agglomeration as Zaandam
    "Hoofddorp-Noord",
}

# Big places just across the border, GeoNames ASCII name -> (country, in-game name)
FOREIGN = [
    ("BE", "Brussels", "Brussel"),
    ("BE", "Antwerp", "Antwerpen"),
    ("BE", "Gent", "Gent"),
    ("BE", "Brugge", "Brugge"),
    ("BE", "Hasselt", "Hasselt"),
    ("BE", "Genk", "Genk"),
    ("DE", "Aachen", "Aken"),
    ("DE", "Koeln", "Keulen"),
    ("DE", "Duesseldorf", "Dusseldorf"),
    ("DE", "Duisburg", "Duisburg"),
    ("DE", "Essen", "Essen"),
    ("DE", "Muenster", "Munster"),
    ("DE", "Osnabrueck", "Osnabruck"),
    ("DE", "Oldenburg", "Oldenburg"),
]


def _rows():
    with open(GEONAMES, encoding="utf-8") as f:
        for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            yield dict(name=r[1], ascii=r[2], lat=float(r[4]), lon=float(r[5]), cc=r[8],
                       fcode=r[7], pop=int(r[14]))


def load_cities(historic=True):
    """historic=True drops places that did not exist in 1839 (see history.py)."""
    rows = list(_rows())
    gone = history.GONE_PLACES if historic else set()
    out = []
    for r in rows:
        if r["cc"] != "NL" or r["pop"] < MIN_POP:
            continue
        if r["fcode"] == "PPLX" or r["name"] in DROP_NL or r["name"] in gone:
            continue
        name = RENAME_NL.get(r["name"], r["name"])
        out.append(dict(name=name, lon=r["lon"], lat=r["lat"], pop=r["pop"], foreign=False))
    if INCLUDE_FOREIGN:
        for cc, gname, ingame in FOREIGN:
            hit = [r for r in rows if r["cc"] == cc and r["ascii"] == gname]
            hit.sort(key=lambda r: -r["pop"])
            r = hit[0]
            out.append(dict(name=ingame, lon=r["lon"], lat=r["lat"], pop=r["pop"], foreign=True))
    for c in out:
        assert len(c["name"]) <= 15, c["name"]
    # most populous first: the game uses the list index as a population rank
    out.sort(key=lambda c: -c["pop"])
    return out


if __name__ == "__main__":
    cs = load_cities()
    print(len(cs), "places;", sum(1 for c in cs if not c["foreign"]), "Dutch")
    for i, c in enumerate(cs):
        print(i, c["name"], c["pop"], round(c["lat"], 3), round(c["lon"], 3), "F" if c["foreign"] else "")
