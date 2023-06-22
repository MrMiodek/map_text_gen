import math
import json
from os import path
import geojson
import shapely
import geopandas as gpd


def projectX(x):
    return x / 360 + 0.5


def projectY(y):
    sin = math.sin(y * math.pi / 180)
    y2 = 0.5 - 0.25 * math.log((1 + sin) / (1 - sin)) / math.pi
    if y2 < 0:
        return 0
    else:
        if y2 > 1:
            return 1
        else:
            return y2


def transformPoint(x, y, extent, z2, tx, ty):
    return [round(extent * (x * z2 - tx)), 
            round(extent * (y * z2 - ty))]


def transform_coordinates(point, x, y, z, extent):
    point[0] = projectX(point[0])
    point[1] = projectY(point[1])
    z2 = 1 << z
    tx = x
    ty = y
    return transformPoint(point[0],point[1], extent, z2, tx, ty)


def geojson_to_vt(geo, x, y, z, extent):
    if type(geo) == float:
        return None
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        transform_coordinates(c, x,y,z,extent), geo2)
    return geo3


def geojson_to_wkt(geo):
    if geo is None:
        return None
    full_wkt = ""
    for feature in geo['features']:
        full_wkt+=feature['properties']['highway']
        wkt = shapely.from_geojson(geojson.dumps(feature['geometry']))
        full_wkt+=f" {str(wkt)}\n"
    return full_wkt


def move_geojson_vt(geo, dx, dy, extent):
    if geo is None:
        return None
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        (c[0]+dx*extent, c[1]+dy*extent), geo2)
    return geo3


def add_geojson_vt(gdf, extent=4096):
    gdf["geojson_vt"] = gdf.apply (lambda row: \
        geojson_to_vt(row['geojson'], row['x'], row['y'], row['z'], extent), axis=1)
    return gdf

def add_wkt(gdf):
    gdf["wkt"] = gdf.apply (lambda row: \
        geojson_to_wkt(row['geojson_vt']), axis=1)
    return gdf


def add_more_formats(city_name, results_dir):
    print(f"Adding more data formats for {city_name}")
    city_dir = path.join(results_dir, city_name)
    print("Reading geojson")
    gdf = gpd.read_file(path.join(city_dir, "rich_gdf.geojson"))
    print("Adding formats")
    gdf = add_geojson_vt(gdf)
    gdf = add_wkt(gdf)
    print("Saving results")
    with open(path.join(city_dir, "multiformat_gdf.geojson"), "w") as multiformat_gdf:
        multiformat_gdf.write(gdf.to_json())
    return gdf
