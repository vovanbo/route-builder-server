import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tornado.ioloop import IOLoop
from tornado.options import parse_command_line, parse_config_file, define, \
    options
from tornado.web import Application as BaseApplication, url

from core import google
from handlers import directions, routes
from settings import BASE_DIR, UUID4_PATTERN, GOOGLE_MAPS_API_KEY
import models

define('host', default='127.0.0.1')
define('port', default=8080)
define('config_file', default='app.conf')
define(
    'db_url',
    default='postgresql://route_builder:somepassword@localhost/route_builder'
)
define('google_maps_api_key', default=GOOGLE_MAPS_API_KEY)

define('debug', default=False, group='application')
define('cookie_secret', default='SOME_SECRET', group='application')


class Application(BaseApplication):
    def __init__(self, handlers=None, default_host='', transforms=None,
                 **settings):
        engine = create_engine(options.db_url, convert_unicode=True,
                               echo=options.debug)
        models.init_db(engine)
        self.db = scoped_session(sessionmaker(bind=engine))
        self.googlemaps = google.AsyncClient(key=options.google_maps_api_key)
        super(Application, self).__init__(
            handlers=handlers, default_host=default_host,
            transforms=transforms, **settings)


def main():
    if os.path.exists(options.config_file):
        parse_config_file(options.config_file)
    parse_command_line()

    app = Application(
        [
            url(r'/directions/?', directions.DirectionsHandler),
            url(r'/routes/?', routes.RoutesHandler),
            url(r'/routes/({uuid})/?'.format(uuid=UUID4_PATTERN),
                routes.RoutesHandler),
        ],
        **options.group_dict('application')
    )
    app.listen(port=options.port, address=options.host)
    logging.info('Listening on http://%s:%d' % (options.host, options.port))

    IOLoop.current().start()


if __name__ == '__main__':
    main()