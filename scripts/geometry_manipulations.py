import math
import json
from os import path
import copy
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
    if type(geo) == float or geo is None:
        return None
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        transform_coordinates(c, x,y,z,extent), geo2)
    return geo3


def geojson_to_wkt(geo):
    if type(geo) == float or geo is None:
        return None
    full_wkt = ""
    for feature in geo['features']:
        full_wkt+=feature['properties']['highway']
        wkt = shapely.from_geojson(geojson.dumps(feature['geometry']))
        full_wkt+=f" {str(wkt)}\n"
    return full_wkt


def move_geojson_vt(geo, dx, dy, extent):
    if type(geo) == float or geo is None:
        return None
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        (c[0]+dx*extent, c[1]+dy*extent), geo2)
    return geo3


#row['geojson']
def add_geojson_vt(gdf, input, extent=4096):
    return gdf.apply (lambda row: \
        geojson_to_vt(row[input], row['x'], row['y'], row['z'], extent), axis=1)
    #gdf["geojson_vt"] 

#gdf["wkt"]
def add_wkt(gdf, input):
    return gdf.apply (lambda row: \
        geojson_to_wkt(row[input]), axis=1)
    #row['geojson_vt']


def line_coords(line):
    return [list(coord) for coord in line.coords]


def simplify_geo(geo, factor):
    if type(geo) == float or geo is None:
        return None
    new_geo = copy.deepcopy(geo)
    for feature in new_geo['features']:
        wkt = shapely.from_geojson(geojson.dumps(feature['geometry']))
        simple_wkt = wkt.simplify(wkt.length*factor, preserve_topology=False)
        if type(simple_wkt) == shapely.geometry.multilinestring.MultiLineString:
            coords = [line_coords(line) for line in simple_wkt.geoms]
            #coords = [line for line in simple_wkt.geoms]
        elif type(simple_wkt) == shapely.geometry.polygon.Polygon:
            coords = [line_coords(simple_wkt.exterior)]
            #coords = simple_wkt.exterior
        else:
            coords = line_coords(simple_wkt)
            #coords = simple_wkt
        feature['geometry']['coordinates'] = coords
    return new_geo

def simplified_geo(gdf, factor, input):
    return gdf.apply (lambda row: \
        simplify_geo(row[input], factor), axis=1)


def add_more_formats(gdf, city_name, results_dir):
    print(f"Adding more data formats for {city_name}")
    city_dir = path.join(results_dir, city_name)
    print("Adding formats")
    gdf['simple'] = simplified_geo(gdf, 0.02, 'geojson')
    gdf['geojson_vt'] = add_geojson_vt(gdf, 'geojson')
    gdf['simple_vt'] = add_geojson_vt(gdf, 'simple')
    gdf['wkt'] = add_wkt(gdf, 'geojson_vt')
    gdf['simple_wkt'] = add_wkt(gdf, 'simple_vt')
    print("Saving results")
    with open(path.join(city_dir, "multiformat_gdf.geojson"), "w") as multiformat_gdf:
        multiformat_gdf.write(gdf.to_json())
    return gdf
