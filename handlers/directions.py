from marshmallow import Schema, fields, validate
from tornado import escape
from webargs.tornadoparser import parser

from handlers.base import BaseHandler


class DirectionsQuerySchema(Schema):
    origin = fields.Str(required=True)
    destination = fields.Str(required=True)
    waypoints = fields.List(fields.Str)
    mode = fields.Str(
        default='driving', validate=validate.OneOf(['driving', 'walking',
                                                    'bicycling', 'transit'])
    )
    language = fields.Str(default='ru')

    class Meta:
        strict = True


class DirectionsHandler(BaseHandler):
    async def get(self, *args, **kwargs):
        args = parser.parse(DirectionsQuerySchema, self.request)
        routes = await self.googlemaps.directions(**args)
        self.finish(escape.json_encode(routes))
