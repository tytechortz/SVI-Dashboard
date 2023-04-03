from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import geopandas as gpd
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from urllib.request import urlopen
import json


app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])

bgcolor = "#f3f3f1"  # mapbox light map land color

header = html.Div("Arapahoe Census Tract SVI Data", className="h2 p-2 text-white bg-primary text-center")

template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}

gdf_2020 = gpd.read_file('2020_CT/ArapahoeCT.shp')
gdf_2016 = gpd.read_file('tl_2016_08_tract/tl_2016_08_tract.shp')
gdf_2016 = gdf_2016.loc[gdf_2016['COUNTYFP'] == '005']
gdf_2016.rename(columns = {'GEOID':'FIPS'}, inplace=True)
gdf_2016['FIPS'] = gdf_2016['FIPS'].apply(lambda x: x[1:])
# print(gdf_2016)
gdf_2018 = gpd.read_file('tl_2018_08_tract/tl_2018_08_tract.shp')
gdf_2018 = gdf_2018.loc[gdf_2018['COUNTYFP'] == '005']
gdf_2018.rename(columns = {'GEOID':'FIPS'}, inplace=True)
gdf_2018['FIPS'] = gdf_2018['FIPS'].apply(lambda x: x[1:])

df_SVI_2020 = pd.read_csv('Colorado_SVI_2020.csv')
df_SVI_2020['YEAR'] = 2020
df_SVI_2018 = pd.read_csv('Colorado_SVI_2018.csv')
df_SVI_2018['YEAR'] = 2018
df_SVI_2016 = pd.read_csv('Colorado_SVI_2016.csv')
df_SVI_2016['YEAR'] = 2016


dfs = [df_SVI_2020, df_SVI_2018, df_SVI_2016] 
df = pd.concat(dfs, ignore_index=True, sort=False)
df = df.loc[df['COUNTY'] == 'Arapahoe']
# print(df)

col_list = list(df_SVI_2020)


def blank_fig(height):
    """
    Build blank figure with the requested height
    """
    return {
        "data": [],
        "layout": {
            "height": height,
            "template": template,
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
        },
    }


app.layout = dbc.Container(
    [
        header,
        dbc.Row(dcc.Graph(id='ct-map', figure=blank_fig(500))),
        dbc.Row([
            dbc.Col([
                html.H6('Opacity')
            ], width=6),
            dbc.Col([
                html.H6('Year')
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Slider(0, 1, value=1,
                    marks={
                        0: {'label': 'Light', 'style': {'color': 'white'}},
                        1: {'label': 'Dark', 'style': {'color': 'white'}},
                    },
                    id = 'opacity',
                ),
            ], width=6),
            dbc.Col([
                dcc.Slider(2016, 2020, value=2020,
                    marks={
                        2016: {'label': '2016', 'style': {'color': 'white'}},
                        2018: {'label': '2018', 'style': {'color': 'white'}},
                        2020: {'label': '2020', 'style': {'color': 'white'}},
                    },
                    id = 'year',
                ),
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.RadioItems(
                    id='category-radio',
                    options=[
                        {'label': 'Total', 'value': 'E_'},
                        {'label': 'Pct.', 'value': 'EP_'},
                        {'label': 'Percentile', 'value': 'EPL_'},
                        {'label': 'Flag', 'value': 'F_'},
                    ],
                    value='E_' 
                ),
            ], width=6),
            dbc.Col([
                dcc.Dropdown(
                    id='variable-dropdown',
                ),
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dcc.RadioItems(
                    id='change-radio',
                    options=[
                        {'label': '2 Year Change', 'value': 2},
                        {'label': '4 Year Change', 'value': 4},
                    ],
                    value=2,
                ),
            ], width=6),
            dbc.Col([
                dcc.Dropdown(
                    id='change-dropdown',
                ),
            ], width=6)
        ]),
        dbc.Row(dcc.Graph(id='ct-2016-map', figure=blank_fig(500))),
        # dbc.Row(dbc.Col(table, className="py-4")),
        dcc.Store(id='year-map-data', storage_type='session'),
        dcc.Store(id='all-map-data', storage_type='session'),
    ],
)


@app.callback(
        Output('variable-dropdown', 'options'),
        Input('category-radio', 'value')
)
def category_options(selected_value):
    print(selected_value)
    # variables = list(lambda x: x, col_list)
    variables = [{'label': i, 'value': i} for i in list(filter(lambda x: x.startswith(selected_value), col_list))]
    # print([{'label': i, 'value': i} for i in col_list[filter(lambda x: x.startswith(selected_value))]])
    return variables 

@app.callback(
    Output('year-map-data', 'data'),
    Input('year', 'value'),
)
def get_data(year):
    print(year)
    df_TOTAL = df.loc[df['YEAR'] == year]
   
    return df_TOTAL.to_json()

@app.callback(
    Output('all-map-data', 'data'),
    Input('year', 'value'),
)
def get_data_all(year):
    
    df_all = df.loc[df['COUNTY'] == 'Arapahoe']
   
   
    return df_all.to_json()

@app.callback(
    Output('ct-map', 'figure'),
    Input('year-map-data', 'data'),
    Input('variable-dropdown', 'value'),
    Input('year', 'value'),
    Input('opacity', 'value')
)
def get_figure(selected_data, dropdown, year, opacity):
  
    df = pd.read_json(selected_data)
    # df['FIPS'] = df["FIPS"].astype(str)
    # df = df_SVI_2016
    df['FIPS'] = df["FIPS"].astype(str)
    
    selection = dropdown
    
    if year == 2016:
        tgdf = gdf_2016.merge(df, on='FIPS')
    elif year == 2018:
        tgdf = gdf_2018.merge(df, on='FIPS')
    else:
        tgdf = gdf_2020.merge(df, on='FIPS')
    tgdf = tgdf.set_index('FIPS')
  

    fig = px.choropleth_mapbox(tgdf, 
                                geojson=tgdf.geometry, 
                                color=selection,                               
                                locations=tgdf.index, 
                                # featureidkey="properties.TRACTCE20",
                                opacity=opacity)

    fig.update_layout(mapbox_style="carto-positron", 
                      mapbox_zoom=10.4,
                      mapbox_center={"lat": 39.65, "lon": -104.8},
                      margin={"r":0,"t":0,"l":0,"b":0},
                      uirevision='constant')


    return fig

@app.callback(
    Output('ct-2016-map', 'figure'),
    Input('all-map-data', 'data'),
    Input('change-dropdown', 'value'),
    Input('variable-dropdown', 'value'),
    Input('change-radio', 'value'),
    Input('year', 'value'),
    Input('opacity', 'value')
)
def get_figure_b(selected_data, change_dropdown, var_dropdown, change, year, opacity):
  
    df_all = pd.read_json(selected_data)
    # print(df_all)
    df_all['FIPS'] = df_all["FIPS"].astype(str)
    # print(df_all)
    selection = var_dropdown

    print(type(selection))
    
    if year == 2016:
        tgdf = gdf_2016.merge(df_all, on='FIPS')
    elif year == 2018:
        tgdf = gdf_2018.merge(df_all, on='FIPS')
    elif year == 2020:
        tgdf = gdf_2020.merge(df_all, on='FIPS')
    f_tgdf = tgdf.set_index('FIPS')
   
    gdf = json.loads(f_tgdf.to_json())

    year_delta = year - change
    print(year_delta)
    start_df = df.loc[df['YEAR'] == year_delta]
    start_df['FIPS'] = start_df["FIPS"].astype(str)
    # print(start_df)
    current_df = df_all.loc[df_all['YEAR'] == 2020]
    # print(current_df)
    change_df = current_df.merge(start_df, on='FIPS')
    # print(change_df)
    if selection is not None:
        var_latest = selection + '_x'
        var_old = selection + '_y'
    # print(var_old)
    # print(var_latest)
    # # print(change_df)
        change_df['diff_var'] = change_df[var_latest] - change_df[var_old]
        print(change_df['diff_var'])
    # test_df = change_df.loc[:, ['FIPS', 'diff_var']]
    # pd.set_option('display.max_rows', None)
    # print(test_df)
    # change_columns = list(change_df)
    # # print(change_columns)
    # # change_df['diff_var']
    # # print(change_df)
    # # print(list(tgdf.columns))
    

    if selection is None:
        fig = px.choropleth_mapbox(tgdf, 
                                geojson=tgdf.geometry, 
                                color=selection,                              
                                locations=tgdf.index, 
                                # featureidkey="properties.TRACTCE20",
                                opacity=opacity)
   
    else:
        fig = go.Figure(
            go.Choroplethmapbox(geojson=gdf, 
                locations=change_df.FIPS, 
                z=change_df['diff_var'],
                # colorscale="Electric",
                zmax = max(change_df['diff_var']),
                zmin = -(max(change_df['diff_var'])),
                marker_opacity=opacity, 
                marker_line_width=.5))
    

    
    fig.update_layout(mapbox_style="carto-positron", 
                    mapbox_zoom=10.4,
                    mapbox_center={"lat": 39.65, "lon": -104.8},
                    margin={"r":0,"t":0,"l":0,"b":0},
                    uirevision='constant')


    return fig

if __name__ == "__main__":
    app.run_server(debug=True, port=8080)