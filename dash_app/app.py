import logging
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pyproj
import os

logger = logging.getLogger(__name__)

IRISH_NATIONAL_GRID_REF = "TM75 / Irish Grid (prepending letter) - epsg:29903"
GA_MEASUREMENT_ID = os.environ.get('GA_MEASUREMENT_ID', None)

# Sidebar style 
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "30px",
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "1rem",
    "background-color": "#f8f9fa",
    "transition": "all 0.3s",
}

SIDEBAR_HIDDEN = {
    "position": "fixed",
    "top": "30px",
    "left": "-18rem",      # move it off screen
    "bottom": 0,
    "width": "18rem",
    "padding": "1rem",
    "background-color": "#f8f9fa",
    "transition": "all 0.3s",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "padding": "2rem",
    "transition": "all 0.3s",
}

CONTENT_EXPANDED = {
    "margin-left": "0",
    "padding": "2rem",
    "transition": "all 0.3s",
}

COLLAPSE_BTN_STYLE = {
        "position": "fixed",
        "top": "10px",
        "left": "10px",
        "zIndex": 2000,
        "padding": "6px 6px",
        "fontSize": "16px",
        "cursor": "pointer",
    }

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

if GA_MEASUREMENT_ID:
    # Inject Google Analytics script into the <head>
    app.index_string = f"""
        <!DOCTYPE html>
        <html>
            <head>
                {{%metas%}}
                <title>{{%title%}}</title>
                {{%favicon%}}
                {{%css%}}
                
                <!-- Google tag (gtag.js) -->
                <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
                <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{GA_MEASUREMENT_ID}');
                </script>
            </head>
            <body>
                {{%app_entry%}}
                <footer>
                    {{%config%}}
                    {{%scripts%}}
                    {{%renderer%}}
                </footer>
            </body>
        </html>
    """

# Mapbox setup
mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{{z}}/{{x}}/{{y}}{{r}}?access_token={access_token}"
try:
    mapbox_token = os.environ.get('MAPBOX_TOKEN')
except:
    print("Failed to locate MAPBOX_TOKEN environmental variable. Register a token at https://docs.mapbox.com/help/getting-started/access-tokens/")
mapbox_ids = ["light-v9", "dark-v9", "streets-v9",
              "outdoors-v9", "satellite-streets-v9"]


epsg_list = []
for epsg in pyproj.get_codes('EPSG', 'CRS'):
    name = pyproj.CRS("epsg:{}".format(epsg)).name
    epsg_list.append("{} - epsg:{}".format(name, epsg))
    if epsg == "29903":
        epsg_list.append(IRISH_NATIONAL_GRID_REF)

MAP_ID = "map-id"
BASE_LAYER_ID = "base-layer-id"
BASE_LAYER_DROPDOWN_ID = "base-layer-drop-down-id"
COORDINATE_CLICK_ID = "coordinate-click-id"
MAX_NUM_OF_ROWS = 1000

# defaults
initial_input_dropdown_value = "TM75 / Irish Grid - epsg:29903"
initial_output_dropdown_value = "WGS 84 - epsg:4326"
initial_data = [	
    {"x_src": 80367, "y_src":84425, "id":"Corrán Tuathail"},
    {"x_src": 335793, "y_src":327689, "id":"Slieve Donard"}
]
initial_data = initial_data + [dict() for i in range(1, MAX_NUM_OF_ROWS - len(initial_data))]
empty_data = [dict() for i in range(1, MAX_NUM_OF_ROWS)]

input_table = dash_table.DataTable(
    id='input-table',
    columns=([{'id': 'x_src', 'name': 'Lat / Northing', 'type': 'numeric'},
             {'id': 'y_src', 'name': 'Lon / Easting', 'type': 'numeric'},
             {'id': 'id', 'name': 'ID', 'type': 'text'}
              ]),
    data=initial_data,
    editable=True, 
    page_action='none',
    )

output_table = dash_table.DataTable(
    id='output-table',
    columns=([{'id': 'x_res', 'name': 'Lat / Northing', 'type': 'numeric'},
             {'id': 'y_res', 'name': 'Lon / Easting', 'type': 'numeric'},
             {'id': 'id', 'name': 'ID', 'type': 'text'}
              ]),
    data=empty_data,
    editable=False,
    page_action='none',
    )

sidebar = html.Div(id='sidebar',
                   className='sidebar',
                   children=[
                        html.H1('Batch Coordinate Converter'),
                        html.Div(f'Convert between any ESPG coordinate systems, in batches of upto {MAX_NUM_OF_ROWS} points.'),
                        html.H2('How to use this tool:'),
                        
                html.Ul(children=[
                        html.Li("Text filter your desired input and output systems. Defaulted to the Irish Grid "),
                        html.Li("Copy and paste coordinate columns from a spreadsheet into the input table"),
                        html.Li("Click 'Convert'"),
                        html.Li("Copy and paste coordinate columns from the output table into your spreadsheet"),
                        html.Li("Use Shift to select multiple cells same as excel"),
                        html.Li("You can paste identifier data into the the 'ID' column for identifying when plotted"),
                        html.Li("Data point markers will be plotted on the map below the table."),
                        html.Li("Clicking on the marker will show a pop up with the coordinates as well as a link out to Google Maps so locations can be validated with satellite and Google Street View."),
                ]),    
                       html.H2('User notes:'),
                       html.Ul(children=[
                       html.Li("For GPS (Lat, Lon) coordinates use WGS 84 - epsg:4326"),
                       html.Li("For Irish users the Irish National Grid with prepending letter can be found in the dropdown as 'TM75 / Irish Grid (prepending  letter) - epsg:29903'"),
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
                        'Convert Data:',
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
                            'Convert', id='convert-btn', n_clicks=0),
                        html.Br(),
                        html.Br(),
                        dbc.Button(
                        'Clear Input Data', id='clear-btn', n_clicks=0)
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
            # dbc.Row([]),
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
                                        checked=mapbox_id == "satellite-streets-v9") for mapbox_id in mapbox_ids]
                                )
                            ]),
                    className='col-12 text-center map'),
            ],
            id='map-container'
        )]
        )
    ])

app.layout = html.Div(children=[
    html.Button("☰", id="toggle-btn", n_clicks=0, style=COLLAPSE_BTN_STYLE),
    sidebar,
    main
])

def irishgrid2xy(grid_ref):
    """
    Converts irish grid reference as string i.e. "N 15904 34671"
    to xy (easting northing) with an origin at the bottem
    left of grid "V"
    """
    logger.debug("irishgrid2xy()")
    grid_ref = grid_ref.strip().upper()
    if " " in grid_ref:
        grid_ref = grid_ref.split(" ")
        letter = grid_ref[0]
        easting = grid_ref[1]
        northing = grid_ref[2]
    else:
        grid_ref_len = len(grid_ref)
        half_grid_ref_len = (grid_ref_len - 1) // 2
        additional_zeros = (5 - half_grid_ref_len)*"0"

        easting_end_index = 1 + half_grid_ref_len
        letter = grid_ref[0]
        easting = grid_ref[1:easting_end_index] + additional_zeros
        northing = grid_ref[easting_end_index:] + additional_zeros


    # 5x5 grid letters, missing I
    grid = [("V", "W", "X", "Y", "Z"),
            ("Q", "R", "S", "T", "U"),
            ("L", "M", "N", "O", "P"),
            ("F", "G", "H", "J", "K"),
            ("A", "B", "C", "D", "E")]

    if len(easting) == 5 & len(northing) == 5:
        for i in range(0,5):
            if letter in grid[i]:
                northing_corr = i
                easting_corr = (grid[i].index(letter))

    easting = '%s%s' % (easting_corr, easting)
    northing = '%s%s' % (northing_corr, northing)

    return easting, northing

def xy2irishgrid(x, y):
    """
    Convert x and y coordinate integers into irish grid reference string
    """
    logger.debug("xy2irishgrid()")
    x = str(x)
    y = str(y)

    grid = [("V", "W", "X", "Y", "Z"),
            ("Q", "R", "S", "T", "U"),
            ("L", "M", "N", "O", "P"),
            ("F", "G", "H", "J", "K"),
            ("A", "B", "C", "D", "E")]
    
    if (len(x) > 6) | (len(y) > 6):
        return "Not in IRE"

    if len(x) < 6:
        easting_corr = '0'
        easting = x
    else:
        easting_corr = x[0]
        easting = x[1:]

    if len(y) < 6:
        northing_corr = '0'
        northing = y
    else:
        northing_corr = y[0]
        northing = y[1:]
    try:
        letter = grid[int(northing_corr)][int(easting_corr)]
    except:
        return "Not in IRE"
    grid_ref = '%s %s %s' % (letter, easting, northing)
    return grid_ref

@app.callback(
    Output('output-table', 'data'),
    Input('convert-btn', 'n_clicks'),
    State('input-table', 'data'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value'),
)
def convert_data(n_clicks, data, input_name, output_name):
    logger.debug("convert_data()")
    logger.info(f"Converting from '{input_name}' to '{output_name}'")

    if not input_name or not output_name:
        return data
    
    input_epsg = input_name[input_name.find('epsg:'):]
    output_epsg = output_name[output_name.find('epsg:'):]
    conversion_transformer = pyproj.Transformer.from_crs(input_epsg, output_epsg)
    # convert output to epsg:4326 for map plotting
    wgs84_transformer = pyproj.Transformer.from_crs(input_epsg, 'epsg:4326')
    for row in data:
        if row=={}:
            break
        try:
            if input_name == IRISH_NATIONAL_GRID_REF:
                row['x_src'], row['y_src'] = irishgrid2xy(row['grid_ref'])
            
            row['x_res'], row['y_res'] = conversion_transformer.transform(row['x_src'], row['y_src'])
            if input_epsg == 'epsg:4326':
                row['lat'], row['lon'] = row['x_src'], row['y_src']
            elif output_epsg == 'epsg:4326':
                row['lat'], row['lon'] = row['x_res'], row['y_res']
            else:
                row['lat'], row['lon'] = wgs84_transformer.transform(row['x_src'], row['y_src'])
            
            if output_name == IRISH_NATIONAL_GRID_REF:
                row['grid_ref'] = xy2irishgrid(row['x_res'], row['y_res'])

        except Exception as e:
            print(e)
    return data


@app.callback(
    Output('markers', 'children'),
    Input('output-table', 'data'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value')
    )
def update_output(data, input_name, output_name):
    logger.debug("update_output()")
    print(f"input_name: {input_name}")
    print(f"output_name: {output_name}")

    if not data or not output_name:
        return []
    
    markers_list = []
    for i, row in enumerate(data):
        if row == {}:
            break
        try:
            marker = dl.Marker(
                position=[row['lat'],row['lon']], 
                children=dl.Popup(
                    children=[
                        html.B("Index:"),
                        html.Br(),
                        i,
                        html.Br(),
                        html.B("id:"),
                        html.Br(),
                        row.get('id'),
                        html.Br(),
                        html.B(input_name),
                        html.Br(),
                        row['grid_ref'] if input_name==IRISH_NATIONAL_GRID_REF else f"{row['x_src']}, {row['y_src']}",
                        html.Br(),
                        html.B(output_name),
                        html.Br(),
                        row['grid_ref'] if output_name==IRISH_NATIONAL_GRID_REF else f"{round(row['x_res'], 2)}, {round(row['y_res'], 2)}",
                        html.Br(),
                        html.A(
                            html.Button(["Open Google Maps ", html.I(className="fa fa-external-link-alt")], className="btn-primary"),
                            href=f"https://www.google.com/maps?q={row['lat']},{row['lon']}&t=k&z=16",
                            target="_blank"
                        )
                    ],
                    className="map_marker_tooltip",
                    ))
            
            markers_list.append(marker)

        except Exception as e:
            logging.exception("Error updating output")

    return markers_list

@app.callback(
    Output('input-table', 'data'),
    Input('clear-btn', 'n_clicks'),
)
def clear_input_data(n_clicks):
    return empty_data

@app.callback(
    Output('input-table', 'columns'),
    Input('input-dropdown', 'value'),
)
def update_input_table_columns(value):
    logger.debug("update_input_table_columns()")
    if value == IRISH_NATIONAL_GRID_REF:
        columns=([
                {'id': 'grid_ref', 'name': 'Grid Ref', 'type': 'text'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    else:
        columns=([{'id': 'x_src', 'name': 'Lat / Northing', 'type': 'numeric'},
                {'id': 'y_src', 'name': 'Lon / Easting', 'type': 'numeric'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    
    return columns

@app.callback(
    Output('output-table', 'columns'),
    Input('output-dropdown', 'value'),
)
def update_output_table_columns(value):
    logger.debug("update_output_table_columns()")
    if value == IRISH_NATIONAL_GRID_REF:
        columns=([
                {'id': 'grid_ref', 'name': 'Grid Ref', 'type': 'text'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    else:
        columns=([{'id': 'x_src', 'name': 'Lat / Northing', 'type': 'numeric'},
                {'id': 'y_src', 'name': 'Lon / Easting', 'type': 'numeric'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    
    return columns

# --- Callback to toggle sidebar ---
@app.callback(
    Output("sidebar", "style"),
    Output("main", "style"),
    Input("toggle-btn", "n_clicks"),
)
def toggle_sidebar(n):
    if n % 2 == 1:  # odd clicks → collapsed
        return SIDEBAR_HIDDEN, CONTENT_EXPANDED
    return SIDEBAR_STYLE, CONTENT_STYLE

if __name__ == '__main__':
    app.run_server(debug=True)
