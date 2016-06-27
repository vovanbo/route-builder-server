from marshmallow_jsonapi import Schema, fields
from marshmallow import pre_dump
from sqlalchemy import func
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from tornado import escape, web

from core.utils import row_to_dict
from handlers.base import BaseHandler
from models import Route


class RouteSchema(Schema):
    id = fields.UUID()
    origin = fields.Dict()
    origin_name = fields.String()
    destination = fields.Dict()
    destination_name = fields.String()
    polyline = fields.Dict()

    class Meta:
        type_ = 'routes'
        strict = True

    @pre_dump(pass_many=True)
    def convert_geojson_to_dict(self, data, many):
        fields = ['origin', 'destination', 'polyline']
        if many:
            for item in data:
                for field in fields:
                    item[field] = escape.json_decode(item[field])
        else:
            for field in fields:
                data[field] = escape.json_decode(data[field])
        return data


class RoutesHandler(BaseHandler):
    async def get(self, route_id=None):
        query_params = (
            Route.id,
            func.ST_AsGeoJSON(Route.origin).label('origin'),
            Route.origin_name,
            func.ST_AsGeoJSON(Route.destination).label('destination'),
            Route.destination_name,
            func.ST_AsGeoJSON(Route.polyline).label('polyline')
        )

        if route_id:
            try:
                result = self.db.query(*query_params).filter(
                    Route.id == route_id).one()
            except MultipleResultsFound:
                msg = 'Multiple results for unique ID is founded.'
                raise web.HTTPError(400, msg, msg)
            except NoResultFound:
                msg = 'Route with ID %s is not found.' % route_id
                raise web.HTTPError(404, msg, msg)
        else:
            result = self.db.query(*query_params).all()

        get_many = not bool(route_id)
        schema = RouteSchema(many=get_many)
        if get_many:
            output = schema.dumps([row_to_dict(r) for r in result])
        else:
            output = schema.dumps(row_to_dict(result))
        self.finish(output.data)
