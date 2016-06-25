from tornado import gen, escape

from handlers.base import BaseHandler


class DirectionsHandler(BaseHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        origin = self.get_query_argument('origin')
        destination = self.get_query_argument('destination')
        google_maps = self.application.google_maps_client
        routes = yield google_maps.directions(origin, destination,
                                              language='ru', alternatives=True)
        self.finish(escape.json_encode(routes))
