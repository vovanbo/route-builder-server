import uuid
from datetime import datetime

from marshmallow_jsonapi import Schema as JSONAPISchema, fields
from marshmallow import Schema, pre_dump, validate
from marshmallow.exceptions import ValidationError
from sqlalchemy import func
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from tornado import escape, web

from core.utils import row_to_dict, dasherize
from handlers.base import BaseHandler
from models import Route


class GeoJSONSchema(Schema):
    type = fields.Str()
    coordinates = fields.Raw()


class RouteInputSchema(JSONAPISchema):
    id = fields.UUID()
    origin = fields.Nested(GeoJSONSchema, required=True)
    origin_name = fields.String(required=True)
    destination = fields.Nested(GeoJSONSchema, required=True)
    destination_name = fields.String(required=True)
    waypoints = fields.List(fields.Float)
    waypoints_names = fields.List(fields.String)
    polyline = fields.Nested(GeoJSONSchema, required=True)
    bounds = fields.Dict()
    created = fields.DateTime(allow_none=True)

    class Meta:
        type_ = 'routes'
        strict = True
        inflect = dasherize


class RouteOutputSchema(JSONAPISchema):
    id = fields.UUID()
    origin = fields.Dict()
    origin_name = fields.String()
    destination = fields.Dict()
    destination_name = fields.String()
    polyline = fields.Dict()
    bounds = fields.Dict()
    created = fields.DateTime()

    class Meta:
        type_ = 'routes'
        strict = True
        inflect = dasherize

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
    def _route_query(self):
        return self.db.query(
            Route.id,
            func.ST_AsGeoJSON(Route.origin).label('origin'),
            Route.origin_name,
            func.ST_AsGeoJSON(Route.destination).label('destination'),
            Route.destination_name,
            func.ST_AsGeoJSON(Route.polyline).label('polyline'),
            Route.bounds,
            Route.created
        )

    async def get(self, route_id=None):
        if route_id:
            try:
                result = self._route_query().filter(
                    Route.id == route_id).one()
            except MultipleResultsFound:
                msg = 'Multiple results for unique ID is founded.'
                raise web.HTTPError(400, msg, msg)
            except NoResultFound:
                msg = 'Route with ID %s is not found.' % route_id
                raise web.HTTPError(404, msg, msg)
        else:
            result = self._route_query().order_by(Route.created.desc()).all()

        get_many = not bool(route_id)
        schema = RouteOutputSchema(many=get_many)
        if get_many:
            output = schema.dumps([row_to_dict(r) for r in result])
        else:
            output = schema.dumps(row_to_dict(result))
        self.finish(output.data)

    async def post(self):
        try:
            args = RouteInputSchema().load(
                escape.json_decode(self.request.body))
        except ValidationError as e:
            raise web.HTTPError(400, escape.json_encode(e.messages),
                                e.messages)
        route_id = uuid.uuid4()
        data = args.data
        new_route = Route(
            id=str(route_id),
            origin=func.ST_GeomFromGeoJSON(escape.json_encode(data['origin'])),
            origin_name=data['origin_name'],
            destination=func.ST_GeomFromGeoJSON(
                escape.json_encode(data['destination'])),
            destination_name=data['destination_name'],
            polyline=func.ST_GeomFromGeoJSON(escape.json_encode(data['polyline'])),
            bounds=data.get('bounds'),
            created=data.get('created') or datetime.utcnow()
        )
        self.db.add(new_route)
        self.db.commit()

        new_route_from_db = self._route_query().filter(
            Route.id == str(route_id)).one()
        schema = RouteOutputSchema()
        output = schema.dumps(row_to_dict(new_route_from_db))
        self.finish(output.data)

    async def options(self, *args, **kwargs):
        self.finish()

    async def delete(self, route_id=None):
        if not route_id:
            msg = 'Delete all routes is not allowed. Pass route ID to DELETE.'
            raise web.HTTPError(400, msg, msg)
        else:
            try:
                route = self.db.query(Route).filter(Route.id == route_id).one()
            except MultipleResultsFound:
                msg = 'Multiple results for unique ID is founded.'
                raise web.HTTPError(400, msg, msg)
            except NoResultFound:
                msg = 'Route with ID %s is not found.' % route_id
                raise web.HTTPError(404, msg, msg)
            self.db.delete(route)
            self.db.commit()
            self.set_status(204)
            self.finish()