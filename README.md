# Batch Coordinate Converter

Batch Coordinate Converter is  Python [Dash](https://dash.plotly.com/) user interface to batch convert coordinates using any tranformation available in [pyproj](https://pyproj4.github.io/pyproj/stable//) 


## Requirements

[Generate your own MAPBOX_TOKEN](https://docs.mapbox.com/help/getting-started/) and set it as an environmental variable on your machine.
```
export MAPBOX_TOKEN=<your_mapbox_token>
```

## Getting Started
Clone the repository and install dependencies.

```
git clone https://github.com/dancasey-ie/batch-coordinate-converter-dash
cd Grid2LatLon
```
You can run the application using docker-compose, docker or as a python application, each detailed below.

For each of the methods below the app will be running at [localhost:8080](http://localhost:8080/).

### Using docker-compose.yml
If you have both [docker](https://www.docker.com/get-started) and [docker-compose](http://localhost:8080/) installed then:
```
docker-compose up -d
```

### Using Dockerfile
If you have [docker](https://www.docker.com/get-started) installed then:
```
docker build -t batch-coordinate-converter .
docker run -it -p 8080:8080 -e MAPBOX_TOKEN=${MAPBOX_TOKEN} --name batch-coordinate-converter
```
### Using Python (venv)

```
python3 -m venv .
source bin/activate
pip install -r dash_app/requirements.txt
python dash_app/app.py

```

## Contributing

Dan Casey
