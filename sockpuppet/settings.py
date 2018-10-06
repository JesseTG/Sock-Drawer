# -*- coding: utf-8 -*-
"""Application configuration."""
import os
import os.path
from simplejson import JSONEncoder


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('SOCKDRAWER_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    CACHE_TYPE = 'redis'  # Can be "memcached", "redis", etc.
    CACHE_DEFAULT_TIMEOUT = 3600 * 72  # 3 days, given in seconds
    TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
    TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET")
    TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    MASHAPE_KEY = os.environ.get("SOCKDRAWER_MASHAPE_KEY")
    API_KEY_PATH = os.environ.get("SOCKDRAWER_API_KEY_PATH")
    CACHE_REDIS_HOST = os.environ.get("SOCKDRAWER_REDIS_HOST", "redis")
    CACHE_REDIS_PORT = os.environ.get("SOCKDRAWER_REDIS_PORT", 6379)
    CACHE_REDIS_PASSWORD = os.environ.get("SOCKDRAWER_REDIS_PASSWORD")
    CACHE_REDIS_DB = os.environ.get("SOCKDRAWER_REDIS_DB", 0)
    SOCKPUPPET_HOST = os.environ.get("SOCKDRAWER_SOCKPUPPET_HOST")
    ZMQ_SOCKET_TYPE = os.environ.get("SOCKPUPPET_ZMQ_SOCKET_TYPE", "REQ")
    ZMQ_CONNECT_ADDR = os.environ.get("SOCKPUPPET_ZMQ_CONNECT_ADDR")
    SOCKPUPPET_DIR = os.environ.get("SOCKPUPPET_DIR", os.path.expanduser("~/code/Sock-Puppet"))
    SOCKPUPPET_MAIN_NAME = os.environ.get("SOCKPUPPET_MAIN_NAME", "main.py")
    SOCKPUPPET_TRAINED_MODEL_PATH = os.environ.get(
        "SOCKPUPPET_TRAINED_MODEL_PATH",
        os.path.expanduser("~/data/trained/trained-25.pkl")
    )

    SOCKPUPPET_WORD_EMBEDDING_PATH = os.environ.get(
        "SOCKPUPPET_WORD_EMBEDDING_PATH",
        os.path.expanduser("~/data/glove/glove.twitter.27B.25d.txt")
    )
    RESTFUL_JSON = {
        "cls": JSONEncoder,
        "for_json": True
    }


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    ZMQ_CONNECT_ADDR = "ipc:///tmp/sockdrawer-sockpuppet-test"
    SOCKPUPPET_HOST = "ipc:///tmp/sockdrawer-sockpuppet-test"
