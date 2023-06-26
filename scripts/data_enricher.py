import json
from os import path
from tqdm import tqdm

import srai.loaders.osm_way_loader as way


tags = way.osm_way_loader.constants.OSM_WAY_TAGS['highway']
geo_types = ["Point", "LineString",
             "LinearRing", "Polygon", 
             "MultiPoint", "MultiLineString", 
             "MultiPolygon", "GeometryCollection"]
NS = { "N":-1, "S":1, "":0}
EW = { "W":-1, "E":1, "":0}


def add_tag_count (row, tag_key, tag_value, source_column = 'geojson'):
    if isinstance(row[source_column], float):
        return 0
    features = row[source_column]['features']
    count = 0
    for feature in features:
        if(feature['properties'][tag_key] == tag_value):
            count = count+1
    return count


def add_tag_geometry_count (row, tag_key, tag_value, geometry, source_column):
    if isinstance(row[source_column], float):
        return 0
    features = row[source_column]['features']
    count = 0
    for feature in features:
        if(feature['properties'][tag_key] == tag_value
           and feature['geometry']['type'] == geometry):
            count = count+1
    return count


def to_python_int(stats):
    for lvl1 in stats:
        for lvl2 in stats[lvl1]:
            stats[lvl1][lvl2] = int(stats[lvl1][lvl2])
    return stats


def get_tag_stats(gdf, osm_filter, source_column):
    tag_stats = {}
    for tag_key in osm_filter:
        if tag_key not in tag_stats:
            tag_stats[tag_key] = {}
        for tag_value in osm_filter[tag_key]:
            gdf[f"{tag_key}_{tag_value}"] = gdf.apply (
                lambda row: add_tag_count(row, tag_key, tag_value, source_column),
                axis=1)
            if tag_value not in tag_stats:
                tag_stats[tag_key][tag_value] = { "total" :
                    gdf[f"{tag_key}_{tag_value}"].sum()}
            for geo_type in geo_types:
                complex_tag = f"{tag_key}_{tag_value}_{geo_type}"
                gdf[complex_tag] = gdf.apply (lambda row:
                    add_tag_geometry_count(row, tag_key, tag_value,
                                           geo_type, source_column), axis=1)
                if geo_type not in tag_stats[tag_key][tag_value]:
                    tag_stats[tag_key][tag_value][geo_type] = gdf[complex_tag].sum()
    return to_python_int(tag_stats)


def get_geo_stats(tag_stats, osm_filter):
    geo_stats = {}
    for tag_key in osm_filter.keys():
        if tag_key not in tag_stats.keys():
            tag_stats[tag_key] = {}
        for tag_value in osm_filter[tag_key]:
            for geo_type in tag_stats[tag_key][tag_value]:
                if geo_type != "total":
                    if geo_type not in geo_stats:
                        geo_stats[geo_type] = { "total" :
                            tag_stats[tag_key][tag_value][geo_type]}
                    else:
                        geo_stats[geo_type]["total"] = \
                            geo_stats[geo_type]["total"] + \
                            tag_stats[tag_key][tag_value][geo_type]
                    geo_stats[geo_type][tag_key][tag_value] = \
                        tag_stats[tag_key][tag_value][geo_type]
    return geo_stats


def has_neighbour(row, dx, dy, gdf, source_column):
    x,y,z,_ = row[['x', 'y', 'z', source_column]]
    nid = f"{x+dx}_{y+dy}_{z}"
    try:
        neighbour_row = gdf.loc[nid]
    except KeyError:
        return False
    return not isinstance(neighbour_row[source_column], float)


def neighbour_count(row):
    count = 0
    for ns in NS:
        for ew in EW:
            dir_name = f"{ns}{ew}"
            if dir_name != "" and row[dir_name]:
                count = count + 1
    return count


def add_direction_columns(gdf, source_column):
    for ns in NS:
        for ew in EW:
            dir_name = f"{ns}{ew}"
            if dir_name != "":
                gdf[dir_name] = gdf.apply (lambda row:
                    has_neighbour(row, EW[ew], NS[ns], gdf, source_column), axis=1)
    gdf["hasGeo"] = gdf.apply (lambda row: not isinstance(row[source_column], float), axis=1)
    gdf["neighbourCount"] = gdf.apply (lambda row: neighbour_count(row), axis=1)
    return gdf


def enrich_data(gdf, city_name, result_path, source_column="geojson"):
    '''Function adding columns with information whether the is data 
    in each direction from tile,
    if tile itself contain data
    and how many neighbours contain data'''
    print(f"Enriching {city_name} data")
    print("Adding direction data")
    gdf = add_direction_columns(gdf, source_column)
    print("Saving enriched geojson")
    if result_path is not None:
        with open(result_path, "w") as full_gdf:
            full_gdf.write(gdf.to_json())
    return gdf


def tag_geometry_data_enrichment(gdf, city_name, results_dir, osm_filter, source_column = "geojson", save_results = True):
    '''Function adding columns with information whether the is data 
    in each direction from tile,
    if tile itself contain data
    and how many neighbours contain data.
    Additionally calculates key/value/geometry statistics and add it to gdf
    WARNING: resulting GeoDataframe may be much larger than original'''
    print(f"Fully enriching {city_name} data")
    city_dir = path.join(results_dir, city_name)
    print("Calculating stats")
    tag_stats = get_tag_stats(gdf, osm_filter, source_column)
    geo_stats = get_geo_stats(tag_stats, osm_filter)
    if save_results:
        with open(path.join(city_dir, "tag_stats.json"), "w") as tag_file:
            json.dump(tag_stats, tag_file)
        with open(path.join(city_dir, "geo_stats.json"), "w") as geo_file:
            json.dump(geo_stats, geo_file)
    print("Adding direction data")
    gdf = add_direction_columns(gdf, source_column)
    print("Saving full geojson")
    if save_results:
        with open(path.join(city_dir, "tag_geometry.geojson"), "w") as full_gdf:
            full_gdf.write(gdf.to_json())
    return gdf, tag_stats, geo_stats
