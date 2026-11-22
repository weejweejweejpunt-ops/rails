#!/usr/bin/env bash
# Download the open geodata that build_map.py turns into the Netherlands map.
# Everything lands in <repo>/geodata (git-ignored, ~25 MB).  Run once.
#
#   GeoNames cities15000      CC-BY 4.0   https://www.geonames.org/
#   Terrarium elevation tiles AWS Open Data (SRTM and other public sources)
#   OpenStreetMap via Overpass ODbL       (c) OpenStreetMap contributors
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
G="${NL_GEODATA:-$REPO/geodata}"
UA="rails-nl-map-script/0.1 (open-source game map generator)"
OV=https://overpass-api.de/api/interpreter
BBOX="50.4,2.0,53.9,9.0"   # south,west,north,east: a little larger than the map window
mkdir -p "$G"/{geonames,terrarium,osm}

echo "== GeoNames"
curl -sS -A "$UA" -o "$G/geonames/cities15000.zip" https://download.geonames.org/export/dump/cities15000.zip
mkdir -p "$G/geonames/extracted" && unzip -o -q "$G/geonames/cities15000.zip" -d "$G/geonames/extracted"

echo "== Terrarium elevation tiles (z=8)"
for x in 129 130 131 132 133 134; do
  for y in 82 83 84 85 86; do
    f="$G/terrarium/8_${x}_${y}.png"
    [ -s "$f" ] || curl -sS -A "$UA" -o "$f" "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/8/$x/$y.png"
  done
done

overpass() {  # name, query body (without the [out:json] header)
  local out="$G/osm/$1.json" try
  for try in 1 2 3 4 5; do
    sleep 10
    code=$(curl -sS -m 400 -A "$UA" -H "Accept: application/json" --data-urlencode "data=[out:json][timeout:240];$2" "$OV" -o "$out" -w "%{http_code}")
    [ "$code" = 200 ] && { echo "   $1: $(stat -c %s "$out") bytes"; return 0; }
    echo "   $1: http $code, retrying ($try)"
  done
  return 1
}

echo "== OpenStreetMap"
overpass coastline "way[\"natural\"=\"coastline\"]($BBOX);out geom;"

RIVERS='Rijn|Nederrijn|Lek|Waal|IJssel|Gelderse IJssel|Maas|Merwede|Nieuwe Merwede|Oude Maas|Nieuwe Maas|Noord|Dordtse Kil|Hollands Diep|Haringvliet|Nieuwe Waterweg|Amer|Bergsche Maas|Afgedamde Maas|Spui|Oude Rijn|Kromme Rijn|Hollandse IJssel|Amstel|Vecht|Overijsselse Vecht|Utrechtse Vecht|Eem|Berkel|Dinkel|Regge|Zwarte Water|Hunze|Ems|Dommel|Roer|Rur|Niers|Lippe|Ruhr|Rhein|Schelde|Westerschelde|Zeeschelde|Leie|Lys|Dender|Dijle|Demer|Zenne|Nete|Grote Nete|Kleine Nete|Meuse|Ourthe|Vesdre|Jeker|Geul|Mark|Dintel|Mark en Dintel|Steenbergse Vliet|Eendracht|Oosterschelde|Kanaal Gent-Terneuzen|Noordzeekanaal|Noord-Zeekanaal|Amsterdam-Rijnkanaal|Twentekanaal|Julianakanaal|Wilhelminakanaal|Zuid-Willemsvaart|Maas-Waalkanaal|Merwedekanaal|Prinses Margrietkanaal|Van Starkenborghkanaal|Eemskanaal|Dortmund-Ems-Kanal|Rhein-Herne-Kanal|Albertkanaal|Ijzer|IJzer|Leopoldkanaal|Ringvaart'
overpass rivers "way[\"waterway\"=\"river\"][\"name\"~\"^($RIVERS)\$\"]($BBOX);out geom;"

LAKES='IJsselmeer|Markermeer|Lauwersmeer|Veluwemeer|Gooimeer|Eemmeer|Wolderwijd|Nuldernauw|Ketelmeer|Vossemeer|Zwarte Meer|Drontermeer|Loosdrechtse Plassen|Reeuwijkse Plassen|Braassemermeer|Kagerplassen|Sneekermeer|Heegermeer|Fluessen|Tjeukemeer|Slotermeer|Haringvliet|Hollands Diep|Volkerak|Brielse Meer|Veerse Meer|Grevelingen|Zoommeer|Markiezaatsmeer|Dollard|Zuidlaardermeer|Krammer|Oostvaardersplassen|Het IJ'
overpass lakes "(relation[\"natural\"=\"water\"][\"name\"~\"^($LAKES)\$\"]($BBOX);way[\"natural\"=\"water\"][\"name\"~\"^($LAKES)\$\"]($BBOX););out geom;"

WATER2='Oosterschelde|Grevelingen|Grevelingenmeer|Veerse Meer|Hollands Diep|Dollard|Markiezaatsmeer|Eems|Lauwersmeer|Zoommeer|Haringvliet|Volkerak|Krammer|Spui'
overpass water2 "(way[\"name\"~\"^($WATER2)\$\"][\"natural\"~\"water|bay|strait\"]($BBOX);relation[\"name\"~\"^($WATER2)\$\"][\"natural\"~\"water|bay|strait\"]($BBOX););out geom;"

DAMS='Afsluitdijk|Houtribdijk|Brouwersdam|Haringvlietdam|Oosterscheldekering|Zandkreekdam|Veerse Gatdam|Sloedam|Philipsdam|Oesterdam|Volkerakdam|Lauwersmeerdijk|Markiezaatskade|Grevelingendam|Zeelandbrug|Kreekrakdam|Ketelbrug|Stormvloedkering Oosterschelde|Noordzeedijk|Dintelsas|Oranjedam|Slaakdam|Mastgat|Roggeplaatdam|Prins Hendrikdam|Waddenzeedijk|Lorentzsluizen|Stevinsluizen|Krammersluizen|Hartelkering|Maeslantkering|Brielse Maasdam|Bathse Spuikanaal|Zoommeerdam'
overpass dams "way[\"name\"~\"^($DAMS)\$\"]($BBOX);out geom;"
echo "done: $G"
