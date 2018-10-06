# -*- coding: utf-8 -*-
"""
    flask.ext.zmq
    ~~~~~~~~~~~~~~

    Adds ZMQ support to your application.

    :copyright: (c) 2013 by Rebill.
    :license: BSD, see LICENSE for more details
"""

__version__ = '0.1.2'

from typing import Optional
import zmq
from zmq import Context, Socket

from flask import Flask, current_app, _app_ctx_stack

# TODO: Package this and submit it to PyPi


class ZMQSocket(object):
    # TODO: Allow multiple instances of this extension to be added
    def __init__(self, app: Optional[Flask]=None):
        # TODO: Pass in the context as an argument
        self.app = app
        self.context = Context.instance()
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        # register extension with app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions["zmq_socket"] = self.socket
        # TODO: Make the name in extensions configurable
        # TODO: How is app.extensions supposed to be used?
        app.teardown_appcontext(self.teardown)

    def _init_socket(self, app: Flask) -> Socket:
        socket = self.context.socket(getattr(zmq, app.config['ZMQ_SOCKET_TYPE']))
        # TODO: Allow either an int or a string here

        socket.connect(app.config['ZMQ_CONNECT_ADDR'])
        # TODO: Set sockopts here
        return socket

    def teardown(self, exception):
        ctx = _app_ctx_stack.top

        if ctx is not None and hasattr(ctx, "zmq_socket"):
            ctx.zmq_socket.close()

    @property
    def socket(self) -> Socket:
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'zmq_socket'):
                ctx.zmq_socket = self._init_socket(current_app)
            return ctx.zmq_socket
