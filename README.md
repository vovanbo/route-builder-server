# Route Builder server application 

(powered by Tornado and PostGIS)

This application use asyncronous fork of `googlemaps` Python package. This fork is supported only directions API calls yet. Located in `core.google.AsyncClient`.

### Requirements:

- Python 3.5
- GeoAlchemy2==0.3.0
- googlemaps==2.4.3
- marshmallow-jsonapi==0.8.0
- marshmallow==2.8.0        # via marshmallow-jsonapi, webargs
- psycopg2==2.6.1
- requests==2.9.1           # via googlemaps
- sqlalchemy==1.0.13
- tornado==4.3
- webargs==1.3.4

### Run:

Note that virtual environment created via pyenv, so it must be installed in your system already.

```shell
$ git clone https://github.com/vovanbo/route-builder-server.git
$ cd route-builder-server
$ pyenv virtualenv 3.5.1 route-builder-server
$ pyenv local route-builder-server
$ pip install -r requirements.txt
$ docker-compose up -d --build
$ PYTHONPATH=. python app.py --google_maps_api_key=<your Google Maps API key>
```
