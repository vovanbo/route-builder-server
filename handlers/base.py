from marshmallow import Schema, fields
from tornado import web, escape


class JSONAPIErrorSchema(Schema):
    status = fields.Integer(required=True)
    source = fields.Dict()
    detail = fields.Raw()


class JSONAPIErrorsSchema(Schema):
    errors = fields.Nested(JSONAPIErrorSchema, many=True)


class BaseHandler(web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def googlemaps(self):
        return self.application.googlemaps

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/vnd.api+json')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

    def write_error(self, status_code, **kwargs):
        schema = JSONAPIErrorsSchema()
        result = {'errors': []}
        if 'exc_info' in kwargs:
            etype, value, traceback = kwargs['exc_info']
            args = getattr(value, 'args', None)
            if args:
                for arg in args:
                    if isinstance(arg, dict) and 'errors' in arg:
                        result = {**result, **arg}
                    else:
                        result['errors'].append({
                            'status': status_code,
                            'detail': arg
                        })
        elif 'message' in kwargs:
            result['errors'].append({
                'status': status_code,
                'detail': kwargs['message']
            })
        if result['errors']:
            output = schema.dumps(result)
            self.finish(output.data)