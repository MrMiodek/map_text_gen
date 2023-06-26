import os
from os import path
from pathlib import Path

import json
import shutil
import ast


import togeojsontiles
import geopandas as gpd
from srai.regionizers import SlippyMapRegionizer
from srai.constants import WGS84_CRS
from srai.loaders.osm_loaders import OSMOnlineLoader
from srai.utils import geocode_to_region_gdf

from shapely.ops import unary_union


def process_city_code(city_code):
    code = city_code
    osm_id = any(char.isdigit() for char in city_code)
    try:
        code = ast.literal_eval(city_code)
    except ValueError:
        pass
    except SyntaxError:
        pass
    return code, osm_id


def get_slippy_boundry(city_code, zoom):
    print("Calculating slippy boundries")
    code, osm_id = process_city_code(city_code)
    city_gdf = geocode_to_region_gdf(code, by_osmid=osm_id)
    regionizer = SlippyMapRegionizer(zoom)
    gdf_slippy = regionizer.transform(city_gdf)
    polygons = gdf_slippy['geometry']
    boundary = unary_union(polygons)
    return boundary, gdf_slippy


def download_osm_data(boundary, osm_filter, result_path):
    print("Downloading OSM data")
    boundary_gdf = gpd.GeoDataFrame(
        geometry=[
            boundary
        ],
        crs=WGS84_CRS,
    )
    loader = OSMOnlineLoader()
    data_gdf = loader.load(boundary_gdf, osm_filter)
    with open(result_path, "w") as file:
        file.write(data_gdf.to_json())


def create_tileset(city_dir, city_name, zoom, tileset_path = None, geojson_path = None):
    if tileset_path is None:
        tileset_path = path.join(city_dir, str(city_name)+'.mbtiles')
    if geojson_path is None:
        tileset_path = path.join(city_dir, str(city_name)+'.geojson')
    print("Creating tileset file")
    tippcanoe_command = f"tippecanoe -o {tileset_path} -Z {zoom} -z {zoom} {geojson_path}"
    os.system(tippcanoe_command)


def decode_tileset(city_dir, tileset_path, tippcanoe_dir = '/usr/local/bin/'):
    print("Decoding tileset file")
    togeojsontiles.mbtiles_to_geojsontiles(
            tippecanoe_dir=tippcanoe_dir,
            tile_dir=city_dir,
            mbtiles_file=tileset_path
        )


def add_geojson (row, city_dir, tile_path = None):
    x,y,_,z = row
    if tile_path is None:
        tile_path = path.join(city_dir, str(z), str(x), f"{y}.geojson")
    if path.isfile(tile_path):
        with open(tile_path, "r") as tile_file:
            tile = json.load(tile_file)
            return tile["features"][0]
    else:
        return None


def download_city_tiles(city_code, city_name, zoom, osm_filter, result_dir, save_results = True):
    """Function used to download osm data, divide it to tiles, and collect it into one geojson file.
    
    returns GeoDataframe
    """
    
    print(f"Starting operations for {city_name}")
    city_dir = path.join(result_dir, city_name)
    Path(city_dir).mkdir(parents=True, exist_ok=True)
    boundry, gdf_slippy = get_slippy_boundry(city_code, zoom)

    geojson_path = path.join(city_dir, f"{city_name}_pre_tiled.geojson")
    mbtiles_path = path.join(city_dir, f"{city_name}.mbtiles")
    result_path = path.join(city_dir, f"{city_name}.geojson")

    download_osm_data(boundry, osm_filter, geojson_path)

    create_tileset(city_dir, city_name, zoom, mbtiles_path, geojson_path)
    os.remove(geojson_path)

    decode_tileset(city_dir, mbtiles_path)
    os.remove(mbtiles_path)

    gdf_slippy['geojson'] = gdf_slippy.apply (lambda row: add_geojson(row, city_dir), axis=1)
    if save_results:
        with open(result_path, "w") as file:
            file.write(gdf_slippy.to_json())
    shutil.rmtree(path.join(city_dir, str(zoom)))
    return gdf_slippy
