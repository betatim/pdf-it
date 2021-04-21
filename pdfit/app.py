import asyncio
import argparse
import logging
import os

import tornado

from . import handler
from . import service


def get_argparser():
    parser = argparse.ArgumentParser(description="PDF it - a simple PDF converter")
    parser.add_argument(
        "--debug", help="Enable debug mode", action="store_true", default=False
    )
    parser.add_argument(
        "--port", help="Port to listen on", default=8080,
    )
    return parser


def start(
    working_directory="/tmp/pdfit",
    port=8080,
    debug=False,
):
    tornado.log.enable_pretty_logging()
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    os.makedirs(working_directory, exist_ok=True)

    http_server = tornado.httpserver.HTTPServer(
        WebApplication(working_directory, debug=debug)
    )
    http_server.listen(port)


def main():
    parser = get_argparser()
    args = parser.parse_args()

    start(debug=args.debug, port=args.port)

    loop = asyncio.get_event_loop()
    loop.run_forever()


class WebApplication(tornado.web.Application):
    def __init__(self, working_directory, debug=False):
        handlers = [
            (r"/", handler.WelcomePage),
            (r"/api", handler.PingHandler),
            (r"/convert/([^/]+)", handler.ConversionHandler),
            (r"/convert/?", handler.ConversionHandler),
            (
                r"/documents/(.*)",
                tornado.web.StaticFileHandler,
                {"path": working_directory},
            ),
            (r"/status/([^/]+)", handler.StatusWebSocket),
        ]

        self.pdf_creator = service.PdfCreator(working_directory)

        settings = dict(working_directory=working_directory, debug=debug)
        tornado.web.Application.__init__(self, handlers, **settings)
