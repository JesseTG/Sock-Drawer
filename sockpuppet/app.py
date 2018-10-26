# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import getpass
import logging
import os
import platform
import socket
from http import HTTPStatus
from typing import Tuple

import zmq
from connexion import FlaskApi, FlaskApp, ProblemException
from flask import Flask, Response, jsonify
from jsonrpc.exceptions import JSONRPCInvalidRequest
from simplejson import JSONDecoder, JSONEncoder
from werkzeug.exceptions import BadRequest, HTTPException

from sockpuppet import commands
from sockpuppet.api import v1
from sockpuppet.errors import BadCharacterError, EmptyNameError
from sockpuppet.extensions import cache, zmq_socket
from sockpuppet.settings import Config, ProdConfig

ZMQ_CAPABILITIES = ("ipc", "pgm", "tipc", "norm", "curve", "gssapi", "draft")


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
    app = connex.app  # type: Flask
    app.logger.setLevel(config_object.LOG_LEVEL)

    log_sysinfo(app, config_object)
    register_config(app, connex, config_object)
    register_extensions(app, config_object)
    register_errorhandlers(app, connex)
    register_shellcontext(connex)
    register_commands(app)

    app.logger.info("Created Flask app %s", app.name)

    return connex


def log_sysinfo(app: Flask, config: Config):
    app.logger.info("ZMQ:")
    app.logger.info("  zmq version: %s", zmq.zmq_version())
    app.logger.info("  pyzmq version: %s", zmq.pyzmq_version())
    app.logger.info("  zmq includes: %s", zmq.get_includes())
    app.logger.info("  zmq library dirs: %s", zmq.get_library_dirs())
    app.logger.info("  has: %s", [c for c in ZMQ_CAPABILITIES if zmq.has(c)])
    app.logger.info("socket:")
    app.logger.info("  fqdn: %s", socket.getfqdn())
    app.logger.info("  has_ipv6: %s", socket.has_ipv6)
    app.logger.info("  hostname: %s", socket.gethostname())
    app.logger.info("  interfaces: %s", [i[1] for i in socket.if_nameindex()])
    app.logger.info("os:")
    app.logger.info("  ctermid: %s", os.ctermid())
    app.logger.info("  cwd: %s", os.getcwd())
    app.logger.info("  groups: %s", os.getgroups())
    app.logger.info("  pgid: %d", os.getpgid(0))
    app.logger.info("  pgrp: %d", os.getpgrp())
    app.logger.info("  pid: %d", os.getpid())
    app.logger.info("  ppid: %d", os.getppid())
    app.logger.info("  priority_process: %d", os.getpriority(os.PRIO_PROCESS, 0))
    app.logger.info("  priority_pgrp: %d", os.getpriority(os.PRIO_PGRP, 0))
    app.logger.info("  priority_user: %d", os.getpriority(os.PRIO_USER, 0))
    app.logger.info("  resuid: ruid=%d, euid=%d, suid=%d", *os.getresuid())
    app.logger.info("  resgid: rgid=%d, egid=%d, sgid=%d", *os.getresgid())
    app.logger.info("  sid: %d", os.getsid(0))
    app.logger.info("  supports_bytes_environ: %s", os.supports_bytes_environ)
    app.logger.info("  uname: %s", os.uname())
    app.logger.info("  cpu_count: %d", os.cpu_count())
    app.logger.info("platform:")
    app.logger.info("  %s", platform.platform())
    app.logger.info("  python_build: %s", platform.python_build())
    app.logger.info("  python_compiler: %s", platform.python_compiler())
    app.logger.info("  python_branch: %s", platform.python_branch())
    app.logger.info("  python_implementation: %s", platform.python_implementation())
    app.logger.info("  python_revision: %s", platform.python_revision())
    app.logger.info("  python_version: %s", platform.python_version())
    app.logger.info("getpass:")
    app.logger.info("  user: %s", getpass.getuser())


def register_config(app: Flask, connex: FlaskApp, config: Config):
    app.config.from_object(config)

    app.logger.info("App config:")
    app.logger.info("  Environment: %s", config.__name__)
    app.logger.info("  APP_DIR = %s", config.APP_DIR)
    app.logger.info("  SPECIFICATION_DIR = %s", config.SPECIFICATION_DIR)
    app.logger.info("  SOCK_TIMEOUT = %dms", config.SOCK_TIMEOUT)
    app.logger.info("  SOCK_HOST = %s", config.SOCK_HOST)
    app.logger.info("  ZMQ_CONNECT_ADDR = %s", config.ZMQ_CONNECT_ADDR)
    app.logger.info("  ZMQ_SOCKET_TYPE = %s", config.ZMQ_SOCKET_TYPE)
    # TODO: Log whether or not secrets were found (but don't actually log them)


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
