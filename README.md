# berlin-geo
Generate "real" Berlin city center map using data from OSM

## Dependencies
- imposm.parser
- osmconvert
- osm2pgsql
- carto
- nik4
- lxml
- pandas
- seaborn

You will also need Berlin's map image for exact bounding box. Easiest way to get this is to let this script generate one. For that you will need to have access to PostGIS database with brandenburg-latest.osm.pbf imported.

You can use [postgis docker image](https://hub.docker.com/r/mdillon/postgis/) to get postgis database and osm2pgsql to import .pbf file into it. There are many tutorials on how to do the import.

## How to
Run `./berlin_geo.py prepare` to download brandenburg-latest.osm.pbf and parse it into .csv file containing specific nodes that we are interested in. Optional parameters does not matter for prepare phase.

If you have background image that you wish to use, now you can run `./berlin_geo.py vis --skip-bg` .

If you want script to generate background image for you, you will need to have [osm-carto's](https://github.com/gravitystorm/openstreetmap-carto) symbols folder in your working directory and PostGIS database with brandenburg osm data. You can provide database connection data to berlin_geo (see script's help). 

Final image is stored in working directory as berlin-center.png.

Have Fun!
