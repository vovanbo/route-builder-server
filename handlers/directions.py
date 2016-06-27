import googlemaps
from marshmallow import Schema, validate
from marshmallow_jsonapi import Schema as JSONAPISchema, fields
from webargs.tornadoparser import parser

from core.google import ApiErrorCode
from handlers.base import BaseHandler


class DirectionsQuerySchema(Schema):
    origin = fields.Str(required=True, validate=lambda s: bool(s))
    destination = fields.Str(required=True, validate=lambda s: bool(s))
    waypoints = fields.List(fields.Str)
    mode = fields.Str(default='driving',
                      validate=validate.OneOf(['driving', 'walking',
                                               'bicycling', 'transit']))
    language = fields.Str(default='ru')

    class Meta:
        strict = True


class DirectionsSchema(JSONAPISchema):
    id = fields.String()
    route = fields.Dict()

    class Meta:
        type_ = 'directions'
        strict = True


class DirectionsHandler(BaseHandler):
    async def get(self, *args, **kwargs):
        args = parser.parse(DirectionsQuerySchema, self.request,
                            locations=('query',))

        error_msg = 'Google Maps API error response: %s'
        try:
            routes = await self.googlemaps.directions(**args)
        except googlemaps.exceptions.ApiError as e:
            self.send_error(
                ApiErrorCode[e.status].value,
                message=error_msg % (e.message if e.message else e.status)
            )
            return
        except googlemaps.exceptions.HTTPError as e:
            self.send_error(e.status_code,
                            message=error_msg % 'HTTP error')
            return
        except googlemaps.exceptions.Timeout as e:
            self.send_error(599, message=error_msg % 'timeout')
            return
        except googlemaps.exceptions.TransportError as e:
            self.send_error(500, message=error_msg % 'transport error')
            return

        result = [{'id': i, 'route': r} for i, r in enumerate(routes)]
        schema = DirectionsSchema(many=True)
        output = schema.dumps(result)
        self.finish(output.data)
