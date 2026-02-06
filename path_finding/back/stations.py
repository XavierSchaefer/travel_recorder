import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from back.dataframe import df

def get_all_stations():
    stations = {
        "stations":{},
        "lats":[],
        "lons":[],
        "names":[]
    }
    for stop_name, lon, lat,id in zip(df["stop_name"], df["stop_lon"],df["stop_lat"],df["parent_station"]):
        if stop_name not in stations:
            stations["stations"][stop_name] = {
                "lon":lon,
                "lat":lat,
                "id":id
            }
            stations["lons"].append(lon)
            stations["lats"].append(lat)
            stations["names"].append(stop_name)

    return stations

def get_station_name_by_id(id):
    for name, id_ in zip(df["stop_name"],df["parent_station"],):
        if id_ == id:
            return name
    return None

def get_station_id_by_name(name):
    return ""

