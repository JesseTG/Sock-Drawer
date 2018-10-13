# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from typing import Tuple
from flask import Flask
from connexion import FlaskApp
from simplejson import JSONDecoder, JSONEncoder

from sockpuppet import commands
from sockpuppet.extensions import api, cache, zmq_socket
from sockpuppet.api import v1
from sockpuppet.settings import Config, ProdConfig


def create_app(config_object: Config=ProdConfig) -> FlaskApp:
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """

    # TODO: Validate config, abort the app if it's not valid
    connex = FlaskApp(
        __name__.split('.')[0],
        specification_dir=config_object.SPECIFICATION_DIR
    )
    connex.add_api(config_object.API_SPEC)
    app = connex.app
    app.config.from_object(config_object)
    register_extensions(app, config_object)
    register_errorhandlers(app)
    register_shellcontext(connex)
    register_commands(app)

    if config_object.DEBUG:
        app.logger.setLevel("INFO")

    return connex


def register_extensions(app: Flask, config: Config):
    """Register Flask extensions."""
    cache.init_app(app)
    zmq_socket.init_app(app)
    app.json_encoder = JSONEncoder
    app.json_decoder = JSONDecoder


def register_errorhandlers(app: Flask):
    """Register error handlers."""
    def render_error(error: Exception):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return str(error), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)


def register_shellcontext(connex: FlaskApp):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'app': connex.app,
            'connex': connex,
            'cache': cache,
            'zmq_socket': zmq_socket,
        }

    connex.app.shell_context_processor(shell_context)


def register_commands(app: Flask):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
