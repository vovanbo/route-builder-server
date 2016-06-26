from tornado.escape import json_encode
from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def googlemaps(self):
        return self.application.googlemaps

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, **kwargs):
        result = {
            'code': status_code,
            'message': kwargs.get('message'),
            'errors': kwargs.get('errors', self._reason),
        }
        self.finish(json_encode(result))
