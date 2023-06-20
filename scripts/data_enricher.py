import geopandas as gpd
import json
from os import path
import srai.loaders.osm_way_loader as way
from tqdm import tqdm


tags = way.osm_way_loader.constants.OSM_WAY_TAGS['highway']
geo_types = ["Point", "LineString", 
             "LinearRing", "Polygon", 
             "MultiPoint", "MultiLineString", 
             "MultiPolygon", "GeometryCollection"]
NS = { "N":-1, "S":1, "":0}
EW = { "W":-1, "E":1, "":0}

def add_tag_count (row, tag):
    if (type(row['geojson']) == float):
        return 0
    features = row['geojson']['features']
    count = 0
    for feature in features:
        if(feature['properties']['highway'] == tag):
            count = count+1
    return count
    
def add_tag_geometry_count (row, tag, geometry):
    if (type(row['geojson']) == float):
        return 0
    features = row['geojson']['features']
    count = 0
    for feature in features:
        if(feature['properties']['highway'] == tag
           and feature['geometry']['type'] == geometry):
            count = count+1
    return count

def to_python_int(stats):
    for lvl1 in stats:
        for lvl2 in stats[lvl1]:
            stats[lvl1][lvl2] = int(stats[lvl1][lvl2])
    return stats

def get_tag_stats(gdf):
    tag_stats = {}
    for tag in tqdm(tags):
        gdf[tag] = gdf.apply (lambda row: add_tag_count(row, tag), axis=1)
        if tag not in tag_stats.keys():
            tag_stats[tag] = { "total" : gdf[tag].sum()}
        for geo_type in geo_types:
            complex_tag = f"{tag}_{geo_type}"
            gdf[complex_tag] = gdf.apply (lambda row: add_tag_geometry_count(row, tag, geo_type), axis=1)
            if geo_type not in tag_stats[tag].keys():
                tag_stats[tag][geo_type] = gdf[complex_tag].sum()
    return to_python_int(tag_stats)


def get_geo_stats(tag_stats):
    geo_stats = {}
    for tag in tag_stats:
        for geo_type in tag_stats[tag]:
            if geo_type != "total":
                if geo_type not in geo_stats.keys():
                    geo_stats[geo_type] = { "total" : tag_stats[tag][geo_type]}
                else:
                    geo_stats[geo_type]["total"] = geo_stats[geo_type]["total"] + tag_stats[tag][geo_type]
                geo_stats[geo_type][tag] = tag_stats[tag][geo_type]
    return geo_stats


def has_neighbour(row, dx, dy, gdf):
    x,y,z, geo = row[['x', 'y', 'z', 'geojson']]
    nid = f"{x+dx}_{y+dy}_{z}"
    try:
        neighbour_row = gdf.loc[nid]
    except KeyError:
        return False
    return type(neighbour_row['geojson']) != float


def neighbour_count(row):
    count = 0
    for ns in NS:
        for ew in EW:
            dir_name = f"{ns}{ew}"
            if dir_name != "" and row[dir_name]:
                count = count + 1
    return count

def add_direction_columns(gdf):
    for ns in NS:
        for ew in EW:
            dir_name = f"{ns}{ew}"
            if dir_name != "":
                print(dir_name)
                gdf[dir_name] = gdf.apply (lambda row: has_neighbour(row, EW[ew], NS[ns], gdf), axis=1)
    gdf["hasGeo"] = gdf.apply (lambda row: type(row['geojson']) != float, axis=1)
    gdf["neighbourCount"] = gdf.apply (lambda row: neighbour_count(row), axis=1)
    return gdf


def enrich_data(city_name, results_dir):
    print(f"Enriching {city_name} data")
    city_dir = path.join(results_dir, city_name)
    print(f"Reading geojson")
    gdf = gpd.read_file(path.join(city_dir, f"{city_name}2.geojson"))
    gdf = gdf.set_index('id')
    print("Calculating stats")
    tag_stats = get_tag_stats(gdf)
    geo_stats = get_geo_stats(tag_stats)
    with open(path.join(city_dir, "tag_stats.json"), "w") as tag_file:
        json.dump(tag_stats, tag_file)
    with open(path.join(city_dir, "geo_stats.json"), "w") as geo_file:
        json.dump(geo_stats, geo_file)
    print("Adding direction data")
    gdf = add_direction_columns(gdf)
    print("Saving enriched geojson")
    with open(path.join(city_dir, "full_gdf.json"), "w") as full_gdf:
        full_gdf.write(gdf.to_json())
    return gdf