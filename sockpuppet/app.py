# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, render_template

from sockpuppet import commands, public, rest
from sockpuppet.extensions import api, cache, debug_toolbar
from sockpuppet.settings import ProdConfig


def create_app(config_object=ProdConfig) -> Flask:
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """

    # TODO: Validate config, abort the app if it's not valid
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    return app


def register_extensions(app: Flask):
    """Register Flask extensions."""
    api.init_app(rest.poc.blueprint)
    cache.init_app(app)
    debug_toolbar.init_app(app)

    # TODO: Can I do this in a more idiomatic way?
    api.add_resource(rest.poc.ProofOfConcept, "/get")

def register_resources(app: Flask):
    api.add_resource(v1.User, "/user")


def register_blueprints(app: Flask):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(rest.poc.blueprint, url_prefix="/api/0")
    return None


def register_errorhandlers(app: Flask):
    """Register error handlers."""
    def render_error(error: Exception):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)


def register_shellcontext(app: Flask):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'app': app
        }

    app.shell_context_processor(shell_context)


def register_commands(app: Flask):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
