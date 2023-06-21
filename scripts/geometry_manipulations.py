import math
import json
import geojson
import shapely

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
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        transform_coordinates(c, x,y,z,extent), geo2)
    return geo3


def geojson_to_wkt(geo):
    full_wkt = ""
    for feature in geo['features']:
        full_wkt+=feature['properties']['highway']
        wkt = shapely.from_geojson(geojson.dumps(feature['geometry']))
        full_wkt+=f" {str(wkt)}\n"
    return full_wkt


def move_geojsonvt(geo, dx, dy, extent):
    geo2 = geojson.loads(json.dumps(geo))
    geo3 = geojson.utils.map_tuples(lambda c: 
        (c[0]+dx*extent, c[1]+dy*extent), geo2)
    return geo3
