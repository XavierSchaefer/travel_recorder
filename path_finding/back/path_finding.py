import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from back.dataframe import df

import numpy as np
from heapq import heappush, heappop
import pandas as pd


def hms_to_seconds(hms: str) -> int:
    if pd.isna(hms) or ":" not in str(hms):
        return None
    h, m, s = map(int, str(hms).split(":"))
    return h * 3600 + m * 60 + s

def normalize_times_per_trip(df: pd.DataFrame, time_col: str) -> pd.Series:
    out = pd.Series(index=df.index, dtype="float64")

    for trip_id, g in df.groupby("trip_id", sort=False):
        g = g.sort_values("stop_sequence")
        base = g[time_col].apply(hms_to_seconds)

        offset = 0
        last = None
        norm = []
        for t in base:
            if t is None:
                norm.append(np.nan)
                continue
            if last is not None and t + offset < last:
                offset += 24 * 3600
            tt = t + offset
            norm.append(tt)
            last = tt

        out.loc[g.index] = norm

    return out


# PREP
NODE_COL = "parent_station" if "parent_station" in df.columns else "stop_id"
df = df.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)

# Normaliser arrival/departure (gestion minuit)
df["dep_s_norm"] = normalize_times_per_trip(df, "departure_time")
df["arr_s_norm"] = normalize_times_per_trip(df, "arrival_time")

# -----------------------
# NOUVEAU : 1 arc par trip_id = (origin -> destination)
# origin = 1er stop du trip
# destination = dernier stop du trip
# poids = arr(last) - dep(first)
# -----------------------
g = df.dropna(subset=[NODE_COL]).groupby("trip_id", sort=False)

edges = pd.DataFrame({
    "u": g[NODE_COL].first(),
    "v": g[NODE_COL].last(),
    "dep_u": g["dep_s_norm"].first(),
    "arr_v": g["arr_s_norm"].last(),
}).reset_index(drop=True)

edges["w"] = edges["arr_v"] - edges["dep_u"]
edges = edges.dropna(subset=["u", "v", "w"])
edges = edges[edges["w"] > 0]  # garder durées positives

# garder le meilleur temps par OD
best_edges = edges.groupby(["u", "v"], as_index=False)["w"].min()
best_edges["w"] = best_edges["w"].astype(int)

# dict d'adjacence
adj = {}
for u, v, w in best_edges.itertuples(index=False):
    adj.setdefault(u, []).append((v, w))

# Dijkstra
def dijkstra( start, goal):
    dist = {start: 0}
    prev = {}
    heap = [(0, start)]

    while heap:
        d, u = heappop(heap)
        if u == goal:
            break
        if d != dist.get(u, np.inf):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, np.inf):
                dist[v] = nd
                prev[v] = u
                heappush(heap, (nd, v))

    if goal not in dist:
        return None, np.inf

    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path, dist[goal]

