import os


BASE_DIR = os.path.dirname(__file__)
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
UUID4_PATTERN = '[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'
