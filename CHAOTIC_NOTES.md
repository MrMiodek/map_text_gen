1. Pobierz z http://download.geofabrik.de/europe/poland.html odpowiednie osm.pbf
2. Korzystając z osmium wydziel potrzbne miasta do osm.pbf
2b. (znajdź narzędzie do bbox)

osmium extract --bbox=16.95,51.05,17.1,51.12 --set-bounds --strategy=smart ~/data/osm/dolnoslaskie/dolnoslaskie-latest.osm.pbf  --output ~/data/tiletest1/wroclaw3.osm.pbf

3. przerób osm.pbf na zbiór kafli

./tilemaker --bbox 16.95,51.05,17.1,51.12 --input ~/data/osm/wroclaw/wroclaw2.osm.pbf --output ~/data/wroclaw3.mbtiles

3b. stwórz własne konfiguracje kafli
--process resources/process-openmaptiles.lua --config resources/config-openmaptiles.json 

tilemaker --input ~/data/osm/wroclaw/wroclaw2.osm.pbf --output ~/data/wroclaw_simple_highway.mbtiles --process resources/process-simple_highway.lua --config resources/config-simple_highway.json 

./tilemaker --input ~/data/osm/wroclaw/wroclaw2.osm.pbf --output ~/data/wroclaw_osm.mbtiles --process resources/process-openmaptiles.lua --config resources/config-openmaptiles.json

./tilemaker --input ~/data/osm/wroclaw/wroclaw2.osm.pbf --output ~/data/wroclaw_example.mbtiles --process resources/process-example.lua --config resources/config-example.json

4. korzystając z tippecanoe przerób kafle na geojsony

tippecanoe-decode file.mbtiles zoom x y

tippecanoe-decode file.mbtiles zoom x y





Przydatne linki:
https://github.com/systemed/tilemaker
https://github.com/systemed/tilemaker/blob/master/docs/CONFIGURATION.md
https://github.com/systemed/tilemaker/blob/master/docs/VECTOR_TILES.md
https://github.com/mapbox/tippecanoe#tippecanoe-decode


    Export into GeoJSON format:

              osmium export data.osm.pbf -o data.geojson

tippecanoe -o ~/data/wroclaw_simple.mbtiles -Z 18 -z 18 ~/data/wroclaw_simple.geojson
osmium export UNITED_STATES.pbf -o UNITED_STATES.geojson --index-type dense_file_array


tippecanoe -e ~/data/wroclaw -d 14 -Z 18 -z 18 ~/data/wroclaw_simple.geojson