import logging
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pyproj
import os

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger()

IRISH_NATIONAL_GRID_REF = "TM75 / Irish Grid (prepending letter) - epsg:29903"
GA_MEASUREMENT_ID = os.environ.get('GA_MEASUREMENT_ID', None)

COLLAPSE_BTN_STYLE = {
    "height": "30px",
    "position": "fixed",
    "top": "10px",
    "left": "10px",
    "zIndex": 2000,
    "fontSize": "18px",
    "cursor": "pointer",
    "background-color": "#6c757d",
    "color": "white",
    "border": "none",
    "border-radius": "5px",
}

# Sidebar style 
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "40px",
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "1rem",
    "background-color": "#f8f9fa",
    "transition": "all 0.3s",
    "overflow":"scroll"
}

SIDEBAR_HIDDEN = {
    "position": "fixed",
    "top": "40px",
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
    logger.error("Failed to locate MAPBOX_TOKEN environmental variable. Register a token at https://docs.mapbox.com/help/getting-started/access-tokens/")
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
INITIAL_INPUT_DROPDOWN_VALUE = "TM75 / Irish Grid - epsg:29903"
INITIAL_OUTPUT_DROPDOWN_VALUE = "WGS 84 - epsg:4326"
INITIAL_DATA = [	
    {"x_src": 80367, "y_src":84425, "id":"Corrán Tuathail"},
    {"x_src": 335793, "y_src":327689, "id":"Slieve Donard"}
]
INITIAL_DATA = INITIAL_DATA + [dict() for i in range(1, MAX_NUM_OF_ROWS - len(INITIAL_DATA))]
empty_data = [dict() for i in range(1, MAX_NUM_OF_ROWS)]

input_table = dash_table.DataTable(
    id='input-table',
    columns=([{'id': 'x_src', 'name': 'Lat / Northing', 'type': 'numeric'},
             {'id': 'y_src', 'name': 'Lon / Easting', 'type': 'numeric'},
             {'id': 'id', 'name': 'ID', 'type': 'text'}
              ]),
    data=INITIAL_DATA,
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
                   style=SIDEBAR_STYLE,
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
                       html.Li("This is an old project, but regularly used. Maintenance has been neglected but improvements are on the way."),
                       html.Li(children=[
                            "The underlying code can be found on  ",
                            html.A("Github", href="https://github.com/dancasey-ie/batch-coordinate-converter-dash", target="_blank"),
                            "."
                       ]),
                       html.Li(children=[
                            "Bugs and feature requests can be raised as ",
                            html.A("Github Issues", href="https://github.com/dancasey-ie/batch-coordinate-converter-dash/issues", target="_blank"),
                            ". ",
                       ]),
                       html.Li(children=[
                            "You can also reach out directly at ",
                            html.A("dancasey.ie", href="https://dancasey.ie", target="_blank"),
                            ". ",
                       ]),
                       ]),    
                   ]
                   )
main = html.Div(
    id='main',
    style=CONTENT_STYLE,
    className='main',
    children=[
        html.Div(
            [dbc.Row([
                dbc.Col(
                    html.Div([
                        'Convert From:',
                        dcc.Dropdown(
                            options=epsg_list,
                            value=INITIAL_INPUT_DROPDOWN_VALUE,
                            id='input-dropdown'),
                        f'Initial input: {INITIAL_INPUT_DROPDOWN_VALUE}']
                    ),
                    className='col-12 col-md-5 text-center d-flex justify-content-center align-items-center',
                    style={"height": "100px"}),
                dbc.Col(
                    html.Div([
                        dbc.Button(
                            'Swap',
                            id='swap-btn',
                            n_clicks=0,
                            className="btn"
                        ),
                        dbc.Button(
                            'Convert', id='convert-btn', n_clicks=0, className="btn"),
                        dbc.Button(
                        'Clear Data', id='clear-btn', n_clicks=0, className="btn")
                    ]
                    ),
                    className='col-12 col-md-2 text-center'),
                dbc.Col(
                    html.Div(children=[
                        'Convert To:',
                        dcc.Dropdown(
                            options=epsg_list,
                            value=INITIAL_OUTPUT_DROPDOWN_VALUE,
                            id='output-dropdown'),
                        f'Initial output: {INITIAL_OUTPUT_DROPDOWN_VALUE}'
                    ]
                    ),
                    className='col-12 col-md-5 text-center d-flex justify-content-center align-items-center',
                    style={"height": "100px"}),
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
    html.Button(
        html.I(className="fa fa-chevron-left"),  # Font Awesome icon
        id="toggle-btn",
        n_clicks=0,
        style=COLLAPSE_BTN_STYLE
    ),
    sidebar,
    main
])

def irishgrid2xy(grid_ref):
    """
    Converts irish grid reference as string i.e. "N 15904 34671"
    to xy (easting northing) with an origin at the bottem
    left of grid "V"
    """
    logger.debug("irishgrid2xy() entry")
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
    
    logger.debug("irishgrid2xy() entry")
    return easting, northing

def xy2irishgrid(x, y):
    """
    Convert x and y coordinate integers into irish grid reference string
    """
    logger.debug("xy2irishgrid() entry")
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

    logger.debug("xy2irishgrid() exit")
    return grid_ref

@app.callback(
    Output('output-table', 'data'),
    Input('convert-btn', 'n_clicks'),
    State('input-table', 'data'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value'),
)
def convert_data(n_clicks, data, input_name, output_name):
    """
    Convert coordinate values in a list of row dictionaries from one CRS to another.

    This function processes a list of input records—each representing a point with
    coordinate fields—and converts their coordinates from the input coordinate
    reference system (CRS) to the output CRS requested by the user. It uses
    `pyproj.Transformer` for CRS transformation and supports special handling for
    Irish National Grid coordinate formats (alphanumeric grid codes vs. numeric
    easting/northing).

    The function also ensures that each row gets a latitude/longitude pair
    (EPSG:4326) for map display, even when the final output CRS differs.

    Parameters
    ----------
    n_clicks : int or None
        The number of times the user has clicked the "Convert" button. Included
        for Dash callback compatibility but not otherwise used in the logic.
    data : list[dict]
        A list of dictionaries representing rows in the input table. Each row may
        contain coordinate fields such as `grid_ref`, `x_src`, and `y_src`.
    input_name : str
        The selected input CRS name, containing an `'epsg:####'` substring or the
        `IRISH_NATIONAL_GRID_REF` constant.
    output_name : str
        The selected output CRS name, containing an `'epsg:####'` substring or the
        `IRISH_NATIONAL_GRID_REF` constant.

    Returns
    -------
    list[dict]
        The same list of row dictionaries, modified in place with added or updated
        coordinate fields:
        - `x_res`, `y_res` for transformed coordinates
        - `lat`, `lon` for WGS84 (EPSG:4326) coordinates
        - `grid_ref` when converting to/from Irish National Grid format

    Notes
    -----
    - If `input_name` or `output_name` is missing, the input data is returned
      unchanged.
    - Irish National Grid coordinates require custom conversion functions
      (`irishgrid2xy`, `xy2irishgrid`).
    - Processing stops early if an empty row (`{}`) is encountered.
    - Errors during row conversion are logged with full stack traces.
    - Debug and info logs provide detailed visibility into CRS paths and
      transformation steps.
    """
    logger.debug("convert_data() entry")

    if not input_name or not output_name:
        return data
    
    data_not_empty = len([r for r in data if r ])
    logger.info(f"Converting {data_not_empty} records from '{input_name}' to '{output_name}'")
    
    input_epsg = input_name[input_name.find('epsg:'):]
    output_epsg = output_name[output_name.find('epsg:'):]
    conversion_transformer = pyproj.Transformer.from_crs(input_epsg, output_epsg)
    # convert output to epsg:4326 for map plotting
    wgs84_transformer = pyproj.Transformer.from_crs(input_epsg, 'epsg:4326')
    count = 0
    for row in data:
        if row=={}:
            break
        try:
            count += 1
            if input_name == IRISH_NATIONAL_GRID_REF:
                logger.debug("Converting input irish grid code to irish grid easting, northing")
                row['x_src'], row['y_src'] = irishgrid2xy(row['grid_ref'])
            
            row['x_res'], row['y_res'] = conversion_transformer.transform(row['x_src'], row['y_src'])
            if input_epsg == 'epsg:4326':
                logger.debug("Copying input epsg:4326 coordinates to lat lon values for map markers")
                row['lat'], row['lon'] = row['x_src'], row['y_src']
            elif output_epsg == 'epsg:4326':
                logger.debug("Copying output epsg:4326 coordinates to lat lon values for map markers")
                row['lat'], row['lon'] = row['x_res'], row['y_res']
            else:
                logger.debug("Get Lat lon")
                row['lat'], row['lon'] = wgs84_transformer.transform(row['x_src'], row['y_src'])
            
            if output_name == IRISH_NATIONAL_GRID_REF:
                logger.debug("Converting input Irish grid easting, northing to Irish grid code")
                row['grid_ref'] = xy2irishgrid(row['x_res'], row['y_res'])
            
        except Exception as e:
            logger.exception("Error:")
    logger.debug("convert_data() exit")
    return data


@app.callback(
    Output('markers', 'children'),
    Input('output-table', 'data'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value')
    )
def update_map_marker(data, input_name, output_name):
    """
    Build a list of Dash Leaflet marker components from geospatial result data.

    This function processes an iterable of row dictionaries containing location
    and coordinate transformation information. For each valid row, a 
    `dl.Marker` with a `dl.Popup` is created that displays details such as:
    - index number
    - record id
    - input coordinate value (formatted according to `input_name`)
    - output coordinate value (formatted according to `output_name`)
    - a link to open the marker location in Google Maps

    Parameters
    ----------
    data : list[dict]
        A list of dictionaries where each dictionary represents a single
        transformed point with keys such as 'lat', 'lon', 'grid_ref',
        'x_src', 'y_src', 'x_res', and 'y_res'. The loop stops early if an
        empty dict `{}` is encountered.
    input_name : str
        The name of the input coordinate system. Determines how the
        input coordinates are displayed in the popup.
    output_name : str
        The name of the output coordinate system. Determines how the
        output coordinates are displayed in the popup.

    Returns
    -------
    list
        A list of `dl.Marker` objects representing each point. An empty list
        is returned if `data` or `output_name` is missing.

    Notes
    -----
    - The function logs debug messages on entry and exit.
    - Any exception while building an individual marker is logged via 
      `logging.exception()`, and processing continues with the next row.
    - Google Maps links open in a new browser tab.
    """
    logger.debug("update_output() entry")

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

    logger.debug("update_output() exit")
    return markers_list

@app.callback(
    Output('input-table', 'data'),
    Input('clear-btn', 'n_clicks'),
)
def clear_input_data(n_clicks):
    logger.debug("clear_input_data() entry")
    logger.debug("clear_input_data() exit")
    return empty_data

@app.callback(
    Output('input-table', 'columns'),
    Input('input-dropdown', 'value'),
)
def update_input_table_columns(value):
    """
    Return the appropriate Dash DataTable column definitions based on the
    selected input coordinate system.

    This function updates the structure of the input table by choosing which
    columns should be displayed when the user selects a specific coordinate
    system from the UI. If the selected system is the Irish National Grid, the
    table will display a single grid reference column. Otherwise, separate
    numeric X/Y coordinate columns are shown.

    Parameters
    ----------
    value : str
        The name of the selected input coordinate system. Typically compared
        against the `IRISH_NATIONAL_GRID_REF` constant.

    Returns
    -------
    list[dict]
        A list of Dash DataTable column definition dictionaries. Each dict
        includes `id`, `name`, and `type` fields describing a table column.

    Notes
    -----
    - Debug messages are logged on function entry and exit.
    - The returned structure is intended for use in the `columns`
      property of a Dash `dash_table.DataTable`.
    """
    logger.debug("update_input_table_columns() entry")
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
    
    logger.debug("update_input_table_columns() exit")
    return columns

@app.callback(
    Output('output-table', 'columns'),
    Input('output-dropdown', 'value'),
)
def update_output_table_columns(value):
    logger.debug("update_output_table_columns() entry")
    if value == IRISH_NATIONAL_GRID_REF:
        columns=([
                {'id': 'grid_ref', 'name': 'Grid Ref', 'type': 'text'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    else:
        columns=([{'id': 'x_res', 'name': 'Lat / Northing', 'type': 'numeric'},
                {'id': 'y_res', 'name': 'Lon / Easting', 'type': 'numeric'},
                {'id': 'id', 'name': 'ID', 'type': 'text'},
                ])
    
    logger.debug("update_output_table_columns() exit")
    return columns

@app.callback(
    Output('output-dropdown', 'value'),
    Output('input-dropdown', 'value'),
    Input('swap-btn', 'n_clicks'),
    State('input-dropdown', 'value'),
    State('output-dropdown', 'value')
)
def swap_coordinates(n_clicks, input_value, output_value):
    """
    Callback function to swap the values of the input and output dropdowns.

    Parameters
    ----------
    n_clicks : int
        Number of times the swap button has been clicked.
    input_value : any
        Current value of the input dropdown.
    output_value : any
        Current value of the output dropdown.

    Returns
    -------
    tuple
        (new_output_value, new_input_value) — the swapped values for each dropdown.
    """
    logger.debug("swap_coordinates() entry")
    logger.debug(f"Before swap: input_value={input_value}, output_value={output_value}")

    # Swap the values
    new_input_value = output_value
    new_output_value = input_value

    logger.debug(f"After swap: input_value={new_input_value}, output_value={new_output_value}")
    logger.debug("swap_coordinates() exit")

    return new_output_value, new_input_value

# --- Callback to toggle sidebar ---
@app.callback(
    Output("sidebar", "style"),
    Output("main", "style"),
    Output("toggle-btn", "children"),  # to change icon dynamically
    Input("toggle-btn", "n_clicks"),
)
def toggle_sidebar(n):
    logger.debug("toggle_sidebar() entry")
    if n % 2 == 1:  # odd → collapsed
        icon = html.I(className="fas fa-chevron-right")  # show expand icon
        return SIDEBAR_HIDDEN, CONTENT_EXPANDED, icon
    # even → expanded
    icon = html.I(className="fas fa-chevron-left")  # show collapse icon
    logger.debug("toggle_sidebar() exit")
    return SIDEBAR_STYLE, CONTENT_STYLE, icon

if __name__ == '__main__':
    app.run_server(debug=True)
