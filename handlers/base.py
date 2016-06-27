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

    def write_error(self, status_code, **kwargs):
        schema = JSONAPIErrorsSchema()
        result = {'errors': []}
        if 'exc_info' in kwargs:
            etype, value, traceback = kwargs['exc_info']
            for messages_attribute in ['messages', 'args']:
                messages = getattr(value, messages_attribute, None)
                if messages:
                    if isinstance(messages, dict):
                        result['errors'].append({
                            'status': status_code,
                            'detail': messages
                        })
                    else:
                        for message in messages:
                            result['errors'].append({
                                'status': status_code,
                                'detail': message
                            })
        elif 'message' in kwargs:
            result['errors'].append({
                'status': status_code,
                'detail': kwargs['message']
            })
        if result['errors']:
            output = schema.dumps(result)
            self.finish(output.data)