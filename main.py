# -*- coding: utf-8 -*-
"""Create an application instance."""
from flask.helpers import get_debug_flag

from sockpuppet.app import create_app
from sockpuppet.settings import DevConfig, ProdConfig

CONFIG = DevConfig if get_debug_flag() else ProdConfig

connex = create_app(CONFIG)
app = connex.app

if __name__ == "__main__":
    connex.run(port=5000)
