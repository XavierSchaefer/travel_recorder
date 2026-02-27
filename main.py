import dash
from dash import dcc
from dash import html ,clientside_callback
import datetime as dt
from flask import request, jsonify
import base64
from dash import callback, Input, Output, State,dash_table
from flask import Flask, Response, request
from dash.exceptions import PreventUpdate
import os
import plotly.graph_objects as go
import numpy as np
from back import dataframe, stations 
from back.path_finding import dijkstra
from back import extract_gares , phrase_controller


app = dash.Dash(__name__,title=f'Travel Recorder',use_pages=False,suppress_callback_exceptions=True)
server = app.server


all_stations = stations.get_all_stations()
names_list = [*set(all_stations["names"])]
#---create map---
fig = go.Figure()

fig.add_trace(go.Scattermap(
    lat=all_stations['lats'],
    lon=all_stations['lons'],
    mode="markers",
    hoverinfo="text",
    text=all_stations["names"],
))

fig.update_layout(
    map_style="open-street-map",
    width=2000,
    height=1500,
)

fig.update_layout(
    map_center={"lat": np.array(all_stations["lats"]).mean(), "lon": np.array(all_stations["lons"]).mean()},
    map_zoom=5
)

app.layout=html.Div(className='wrapper-main',children=[
    dcc.Store(id="station_data", data = all_stations),
    # dcc.Dropdown(id="depart",options=names_list,placeholder="Départ", multi=False),
    # dcc.Dropdown(id="arrivee",options=names_list,placeholder="Arrivée",  multi=False),
    dcc.Input(id="phrase",placeholder="Entrez votre demmande", debounce=True),
    html.Div(id="outputs"),
    html.Div(className="map", children=[
        dcc.Graph(id='map_graph',figure=fig,config={"displaylogo": False}),
    ])
    
])



#------------------- path finding by dropdonws CALLBACK ---------------------
@callback(
    Output("station_data", "data"),
    Output("map_graph", "figure"),
    Output('outputs',"children"),
    Input("depart", "value"),
    Input("arrivee", "value"),
    State("station_data","data"),
    State("map_graph", "figure"),
    prevent_initial_call=True,
)
def find_path_by_name(depart, arrivee, store,fig): 
    if depart == None or arrivee == None:
        raise PreventUpdate
    
    id_depart = store["stations"][depart]["id"]
    id_arrivee = store["stations"][arrivee]["id"]
    #trouve le chemin le plus court
    path, total_s = dijkstra(id_depart, id_arrivee)

    highlight_lat = []
    highlight_lon = []
    names = []
    colors = []
    for item in path:
        name_ = stations.get_station_name_by_id(item)
        highlight_lat.append(store["stations"][name_]["lat"])
        highlight_lon.append(store["stations"][name_]["lon"])
        names.append(name_)
        colors.append("#eb6262")
    
    
    #afficher le bins 
    fig = go.Figure()

    fig.add_trace(go.Scattermap(
        lat=highlight_lat,
        lon=highlight_lon,
        mode="markers+lines",
        hoverinfo="text",
        text=names,
        marker_color = colors
    ))

    fig.update_layout(
        map_style="open-street-map",
        width=2000,
        height=1500,
    )

    fig.update_layout(
        map_center={"lat": np.array(highlight_lat).mean(), "lon": np.array(highlight_lon).mean()},
        map_zoom=5
    )

    #convertir le temps en heures ou minutes 
    if total_s < 3600:
        output_string = f"Temps de trajet = {round(total_s/60)} minutes"
    else:
        output_string = f"Temps de trajet = {round(total_s/3600, 2)} heures"


    return store, fig, output_string

#------------------- path finding by phrase CALLBACK ---------------------
@callback(
    Output("station_data", "data",allow_duplicate=True),
    Output("map_graph", "figure",allow_duplicate=True),
    Output('outputs',"children",allow_duplicate=True),
    State("map_graph", "figure"),
    Input("phrase", "value"),
    State("station_data","data"),
    prevent_initial_call=True,
)
def get_phrase(fig,phrase,store):
    if phrase == None :
        return dash.no_update, dash.no_update, "Veuillez entrer une phrase"
    
    trip_data = phrase_controller.phrase_to_trip(phrase)
    if type(trip_data) == str:
        return dash.no_update, dash.no_update, trip_data

    path = trip_data['best_trip']['path']
    total_s = trip_data['best_trip']['total_s']
    print(path)
    if path == None:
        return dash.no_update, dash.no_update, "Gare non trouvée"
    highlight_lat = []
    highlight_lon = []
    names = []
    colors = []
    for item in path:
        name_ = stations.get_station_name_by_id(item)
        highlight_lat.append(store["stations"][name_]["lat"])
        highlight_lon.append(store["stations"][name_]["lon"])
        names.append(name_)
        colors.append("#eb6262")
    
    
    #afficher le bins 
    fig = go.Figure()

    fig.add_trace(go.Scattermap(
        lat=highlight_lat,
        lon=highlight_lon,
        mode="markers+lines",
        hoverinfo="text",
        text=names,
        marker_color = colors
    ))

    fig.update_layout(
        map_style="open-street-map",
        width=2000,
        height=1500,
    )

    fig.update_layout(
        map_center={"lat": np.array(highlight_lat).mean(), "lon": np.array(highlight_lon).mean()},
        map_zoom=5
    )

    #convertir le temps en heures ou minutes 
    if total_s < 3600:
        output_string = f"Temps de trajet = {round(total_s/60)} minutes"
    else:
        output_string = f"Temps de trajet = {round(total_s/3600, 2)} heures"


    return store, fig, output_string

if __name__ == "__main__":
    app.run(debug=True, port = 8090)

