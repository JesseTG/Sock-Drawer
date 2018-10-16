# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from typing import Tuple
from flask import Flask, Response, jsonify
from http import HTTPStatus
from connexion import FlaskApp, FlaskApi, ProblemException
from simplejson import JSONDecoder, JSONEncoder
from werkzeug.exceptions import HTTPException, BadRequest
from jsonrpc.exceptions import JSONRPCInvalidRequest
from sockpuppet import commands
from sockpuppet.extensions import api, cache, zmq_socket
from sockpuppet.api import v1
from sockpuppet.settings import Config, ProdConfig
from sockpuppet.errors import EmptyNameError, BadCharacterError


def create_app(config_object: Config=ProdConfig) -> FlaskApp:
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """

    # TODO: Validate config, abort the app if it's not valid
    connex = FlaskApp(
        __name__.split('.')[0],
        specification_dir=config_object.SPECIFICATION_DIR,
        debug=config_object.DEBUG
    )
    api = connex.add_api(
        config_object.API_SPEC,
        validate_responses=config_object.VALIDATE_RESPONSES,
        resolver_error=BadRequest
    )  # type: FlaskApi
    app = connex.app

    app.config.from_object(config_object)
    register_extensions(app, config_object)
    register_errorhandlers(app, connex)
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


def register_errorhandlers(app: Flask, connex: FlaskApp):
    """Register error handlers."""

    connex.add_error_handler(BadRequest, v1.handle_http_exception(JSONRPCInvalidRequest))

    @app.after_request
    def transform(response: Response) -> Response:
        if response.status_code != HTTPStatus.OK:
            jsonrpc = jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32602,
                    "message": "Oops",
                    "data": response.json
                }
            })
            jsonrpc.status_code = response.status_code

            return jsonrpc
        else:
            return response
    # interesting parameters here:
    # connex.resolver_error
    # connex.common_error_handler
    # connex.auth_all_paths


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
