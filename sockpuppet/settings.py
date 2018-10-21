# -*- coding: utf-8 -*-
"""Application configuration."""
import os
import os.path
from simplejson import JSONEncoder


def load_secret(name: str, required=True) -> str:
    available = name in os.environ  # type: bool

    if (not available) and required:
        raise EnvironmentError(f"Required {name} to be set in the environment, not found")
    elif (not available) and not required:
        return ""

    path = os.environ[name]  # type: str
    exists = os.path.exists(path)  # type: bool

    if (not exists) and required:
        # If we don't have it but we need it...
        raise FileNotFoundError(f"File {path} not found")
    elif (not exists) and (not required):
        # If we don't have it and we don't need it...
        return ""

    with open(path, "r") as secret:
        return secret.readline().strip()

# TODO: Replace all path strings with Pathlib.Path


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get(
        'SOCKDRAWER_SECRET_KEY',
        load_secret("SOCKDRAWER_SECRET_KEY_FILE", required=False)
    )
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    API_SPEC = os.environ.get("SOCKDRAWER_API_SPEC", "v1-swagger.yml")
    SPECIFICATION_DIR = os.environ.get("SOCKDRAWER_SPECIFICATION_DIR", "api/")
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    CACHE_TYPE = 'redis'  # Can be "memcached", "redis", etc.
    CACHE_DEFAULT_TIMEOUT = 3600 * 72  # 3 days, given in seconds
    TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
    TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET")
    TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    MASHAPE_PROXY_SECRET = os.environ.get(
        "SOCKDRAWER_MASHAPE_PROXY_SECRET",
        load_secret("SOCKDRAWER_MASHAPE_PROXY_SECRET_FILE", required=False)
    )
    CACHE_REDIS_HOST = os.environ.get("SOCKDRAWER_REDIS_HOST", "redis")
    CACHE_REDIS_PORT = int(os.environ.get("SOCKDRAWER_REDIS_PORT", 6379))
    CACHE_REDIS_PASSWORD = os.environ.get("SOCKDRAWER_REDIS_PASSWORD")
    CACHE_REDIS_DB = os.environ.get("SOCKDRAWER_REDIS_DB", 0)
    SOCK_HOST = os.environ.get("SOCKDRAWER_SOCK_HOST")
    ZMQ_SOCKET_TYPE = os.environ.get("SOCKDRAWER_ZMQ_SOCKET_TYPE", "REQ")
    ZMQ_CONNECT_ADDR = os.environ.get("SOCKDRAWER_ZMQ_CONNECT_ADDR")
    SOCK_DIR = os.environ.get("SOCK_DIR", os.path.expanduser("~/code/Sock"))
    SOCK_MAIN_NAME = os.environ.get("SOCK_MAIN_NAME", "main.py")
    SOCK_TRAINED_MODEL_PATH = os.environ.get(
        "SOCK_TRAINED_MODEL_PATH",
        os.path.expanduser("~/data/trained/trained-25.pkl")
    )

    # TODO: Condense ZMQ_CONNECT_ADDR and SOCK_HOST
    SOCK_WORD_EMBEDDING_PATH = os.environ.get(
        "SOCK_WORD_EMBEDDING_PATH",
        os.path.expanduser("~/data/glove/glove.twitter.27B.25d.txt")
    )

    VALIDATE_RESPONSES = False
    MAX_URL_LENGTH = int(os.environ.get("SOCKDRAWER_MAX_URL_LENGTH", 1024))


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    VALIDATE_RESPONSES = True


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    ZMQ_CONNECT_ADDR = "ipc:///tmp/sockdrawer-sock-test"
    SOCK_HOST = "ipc:///tmp/sockdrawer-sock-test"
    VALIDATE_RESPONSES = True
