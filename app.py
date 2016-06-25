import logging
import os
from datetime import timedelta

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.options import parse_command_line, parse_config_file, define, \
    options
from tornado.web import Application as BaseApplication, url

from core.google import AsyncClient
from handlers import directions
from settings import BASE_DIR, UUID4_PATTERN, GOOGLE_MAPS_API_KEY

define('host', default='127.0.0.1')
define('port', default=8080)
define('config_file', default='app.conf')

define('debug', default=False, group='application')
define('cookie_secret', default='SOME_SECRET', group='application')


class Application(BaseApplication):
    def __init__(self, handlers=None, default_host='', transforms=None,
                 **settings):
        self.google_maps_client = AsyncClient(key=GOOGLE_MAPS_API_KEY)
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
        ],
        static_path=os.path.join(BASE_DIR, 'static'),
        **options.group_dict('application')
    )
    app.listen(port=options.port, address=options.host)
    logging.info('Listening on http://%s:%d' % (options.host, options.port))

    IOLoop.current().start()


if __name__ == '__main__':
    main()