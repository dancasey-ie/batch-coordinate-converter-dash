from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pyproj
import os

app = Dash(__name__,
           url_base_pathname="/batch-coordinate-converter/",
           meta_tags=[{"name": "viewport",
                       "content": "width=device-width, initial-scale=1"}],
           external_stylesheets=[
               dbc.themes.BOOTSTRAP, 'https://pro.fontawesome.com/releases/v5.10.0/css/all.css'],
           prevent_initial_callbacks=True,
           suppress_callback_exceptions=True,
           update_title=None)
server = app.server
app.title = 'Batch Coordinate Converter'

epsg_list = []
for epsg in pyproj.get_codes('EPSG', 'CRS'):
    name = pyproj.CRS("epsg:{}".format(epsg)).name
    epsg_list.append("{} - epsg:{}".format(name, epsg))

# Mapbox setup
mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{{z}}/{{x}}/{{y}}{{r}}?access_token={access_token}"
try:
    mapbox_token = os.environ.get('MAPBOX_TOKEN')
except:
    print("Failed to locate MAPBOX_TOKEN environmental variable. Register a token at https://docs.mapbox.com/help/getting-started/access-tokens/")
mapbox_ids = ["light-v9", "dark-v9", "streets-v9",
              "outdoors-v9", "satellite-streets-v9"]

MAP_ID = "map-id"
BASE_LAYER_ID = "base-layer-id"
BASE_LAYER_DROPDOWN_ID = "base-layer-drop-down-id"
COORDINATE_CLICK_ID = "coordinate-click-id"

# defaults
initial_input_dropdown_value = "TM75 / Irish Grid - epsg:29903"
initial_output_dropdown_value = "WGS 84 - epsg:4326"
initial_data = [	
    {"x": 80367, "y":84425, "id":"Corrán Tuathail"},
    {"x": 335793, "y":327689, "id":"Slieve Donard"}
]
empty_data = [dict() for i in range(1, 200)]
initial_data = initial_data + empty_data

input_table = dash_table.DataTable(
    id='input-table',
    columns=([{'id': 'x', 'name': 'X / Lat', 'type': 'numeric'},
             {'id': 'y', 'name': 'Y / Lon', 'type': 'numeric'},
             {'id': 'id', 'name': 'ID', 'type': 'text'}
              ]),
    data=initial_data,
    editable=True)

output_table = dash_table.DataTable(
    id='output-table',
    columns=([{'id': 'x', 'name': 'X / Lat', 'type': 'numeric'},
             {'id': 'y', 'name': 'Y / Lon', 'type': 'numeric'},
             {'id': 'id', 'name': 'ID', 'type': 'text'}
              ]),
    data=[dict() for i in range(1, 200)],
    editable=False)

sidebar = html.Div(id='sidebar',
                   className='sidebar',
                   children=[
                        html.H1('Batch Coordinate Converter'),
                        html.Div('Convert between any ESPG coordinate systems, in batches of upto 200 points.'),
                        html.H2('How to use this tool:'),
                        
                html.Ul(children=[
                        html.Li("Text filter your desired input and output systems. Defaulted to the Irish Grid "),
                        html.Li("Copy and paste coordinate columns from a spreadsheet into the input table"),
                        html.Li("Click 'Convert'"),
                        html.Li("Copy and paste coordinate columns from the output table into your spreadsheet"),
                        html.Li("Use Shift to select multiple cells same as excel"),
                        html.Li("You can paste identifier data into the the 'ID' column for identifying when plotted"),
                        html.Li("Data points will be plotted on the map below the table."),
                ]),    
                       html.H2('User notes:'),
                       html.Ul(children=[
                       html.Li("For GPS (Lat, Lon) coordinates use WGS 84 - epsg:4326"),
                       html.Li("This is an old project that I do not actively maintain but am happy to keep alive as people seem to be using it."),
                       html.Li(children=[
                            "The underlying code can be found on  ",
                            html.A("Github", href="https://github.com/dancasey-ie/batch-coordinate-converter-dash", target="_blank"),
                            "."
                       ]),
                       html.Li(children=[
                            "Please reach out if you would like further development. ",
                            html.A("dancasey.ie", href="https://dancasey.ie", target="_blank"),
                            "."
                       ]),
                       ]),    
                   ]
                   )
main = html.Div(
    id='main',
    className='main',
    children=[
        html.Div(
            [dbc.Row([
                dbc.Col(
                    html.Div([
                        'Convert from:',
                        dcc.Dropdown(
                            options=epsg_list,
                            value=initial_input_dropdown_value,
                            id='input-dropdown'),
                        f'Initial input: {initial_input_dropdown_value}']
                    ),
                    className='col-12 col-md-5 text-center'),
                dbc.Col(
                    html.Div([
                        dbc.Button(
                            'Convert', id='convert-btn', n_clicks=0)
                    ]
                    ),
                    className='col-12 col-md-2 text-center'),
                dbc.Col(
                    html.Div(children=[
                        'Convert to:',
                        dcc.Dropdown(
                            options=epsg_list,
                            value=initial_output_dropdown_value,
                            id='output-dropdown'),
                        f'Initial output: {initial_output_dropdown_value}'
                    ]
                    ),
                    className='col-12 col-md-4 text-center'),
            ]),
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            html.B(
                                "Input Table"), ]
                        ),
                        className='col-6 col-md-5 text-center'),
                    dbc.Col(
                        html.Div(children=[
                            html.B(
                                "Output Table"),
                        ]
                        ),
                        className='col-6 col-md-4 offset-md-2 text-center'),
                ]),
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            input_table]
                        ),
                        className='col-6 col-md-5 text-center'),
                    dbc.Col(
                        html.Div(children=[

                            output_table,
                        ]
                        ),
                        className='col-6 col-md-4 offset-md-2  text-center'),
                ],
                id='table-container'
            ),
            dbc.Row([
                    # dbc.Col(
                    #     dbc.Button(
                    #         'View on Map', id='view-on-map-btn', n_clicks=0),
                    #     className='col-12 col-md-2 offset-md-5'
                    # )
                    ]),
                dbc.Row([
                    dbc.Col(
                        dl.Map(id=MAP_ID,
                               style={'width': '100%', 'height': '500px'},
                               center=[53.0, -8.0],
                               zoom=2,
                               children=[
                                   dl.LayerGroup(id="markers"),
                                   dl.LocateControl(options={'locateOptions': {
                                       'enableHighAccuracy': True}}),
                                   dl.MeasureControl(position="topleft", primaryLengthUnit="kilometers", primaryAreaUnit="hectares",
                                                     activeColor="#214097", completedColor="#972158"),
                                   dl.LayersControl(
                                       [dl.BaseLayer([
                                           dl.TileLayer(url=mapbox_url.format(
                                               id=mapbox_id, 
                                               access_token=mapbox_token
                                               )),

                                       ],
                                           name=mapbox_id,
                                           checked=mapbox_id == "outdoors-v9") for mapbox_id in mapbox_ids]
                                   )
                               ]),
                        className='col-12 text-center map'),
                ],
                id='map-container'
            )]
        )
    ])

app.layout = html.Div(children=[
    sidebar,
    main
])


@app.callback(
    Output('output-table', 'data'),
    Input('convert-btn', 'n_clicks'),
    State('input-table', 'data'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value'),
)
def convert_data(n_clicks, data, input_name, output_name):
    print("convert_data() entry")
    if input_name != None and output_name != None:
        input_epsg = input_name[input_name.find('epsg:'):]
        output_epsg = output_name[output_name.find('epsg:'):]
        transformer = pyproj.Transformer.from_crs(input_epsg, output_epsg)
        for row in data:
            if row=={}:
                break
            try:
                row['x'], row['y'] = transformer.transform(row['x'], row['y'])
            except Exception as e:
                print(e)
    return data


@app.callback(
    Output('markers', 'children'),
    Input('output-table', 'data'),
    State('output-dropdown', 'value'),)
def update_output(data, output_name):
    print("update_output() entry")
    markers_list = []
    if output_name != None:
        output_epsg = output_name[output_name.find('epsg:'):]
        if output_epsg != 'epsg:4326':
            # convert output to epsg:4326 for map plotting
            transformer = pyproj.Transformer.from_crs(output_epsg, 'epsg:4326')
            for row in data:
                if row=={}:
                    break
                try:
                    row['lat'], row['lon'] = transformer.transform(
                        row['x'], row['y'])
                except Exception as e:
                    print(e)
        else:
            for row in data:
                if row=={}:
                    break
                row['lat'], row['lon'] = row['x'], row['y']

        for i, row in enumerate(data):
            if row == {}:
                break
            try:
                marker = dl.Marker(position=[row['lat'], row['lon']],
                                children=dl.Tooltip(
                [html.B(f"Index: {i+1}"),
                html.Br(),
                f"Id: {row.get('id')}",
                ]))
                markers_list.append(marker)

            except Exception as e:
                        print(e)

    return markers_list


if __name__ == '__main__':
    app.run_server(debug=True)
