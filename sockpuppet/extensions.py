# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_restful import Api

api = Api()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
