# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import csv
import os
import subprocess
import sys
import time
from random import randint
from typing import Callable, Dict, Sequence, Union

import pytest
import zmq
from connexion import FlaskApp
from flask import Flask
from pytest import Item, Session
from webtest import TestApp
from zmq import Context, Socket

import sockpuppet.utils
from sockpuppet.app import create_app
from sockpuppet.settings import TestConfig

from .marks import *

# must write fixtures to fake some mashape headers
pytest_plugins = 'pytester'


def pytest_report_header(config, startdir):

    return (
        f"SOCK_TRAINED_MODEL_PATH: {TestConfig.SOCK_TRAINED_MODEL_PATH}",
        f"SOCK_WORD_EMBEDDING_PATH: {TestConfig.SOCK_WORD_EMBEDDING_PATH}",
        f"SOCK_HOST: {TestConfig.SOCK_HOST}",
        f"SOCK_DIR: {TestConfig.SOCK_DIR}",
        f"SOCK_MAIN_NAME: {TestConfig.SOCK_MAIN_NAME}",
    )


@pytest.fixture(scope="session")
def app() -> FlaskApp:
    """An application for the tests."""
    connex = create_app(TestConfig)
    _app = connex.app
    _app.testing = True
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def client(app: Flask):
    test_client = app.test_client()

    yield test_client


@pytest.fixture(scope="session")
def sockpuppet_server():
    env = dict(os.environ)  # type: Dict[str, str]

    env["SOCK_TRAINED_MODEL_PATH"] = TestConfig.SOCK_TRAINED_MODEL_PATH
    env["SOCK_WORD_EMBEDDING_PATH"] = TestConfig.SOCK_WORD_EMBEDDING_PATH
    env["SOCK_SERVER_BIND_ADDRESS"] = TestConfig.SOCK_HOST

    context = Context.instance()  # type: Context
    socket = context.socket(zmq.REQ)  # type: Socket

    with context.socket(zmq.REQ) as socket:
        socket.heartbeat_ivl = 2000
        socket.heartbeat_timeout = 2000
        socket.connect(TestConfig.SOCK_HOST)

        # Don't put process in a with statement; when exiting, it waits for the subprocess
        # (and we don't want to do that, we want to kill it)
        process = subprocess.Popen(
            (sys.executable, TestConfig.SOCK_MAIN_NAME),  # python main.py
            env=env,
            cwd=TestConfig.SOCK_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        assert process is not None

        ping = {
            "jsonrpc": "2.0",
            "id": randint(sockpuppet.utils.MIN_JSON_INT, sockpuppet.utils.MAX_JSON_INT),
            "method": "ping"
        }
        socket.send_json(ping)

        events = socket.poll(30 * 1000)
        assert events > 0

        pong = socket.recv_json()

        assert isinstance(pong, Dict)

        assert pong["jsonrpc"] == ping["jsonrpc"]
        assert pong["id"] == ping["id"]
        assert pong["result"] == "pong"

    yield process

    process.terminate()


@pytest.fixture(scope="session")
def testapp(app: Flask):
    """A Webtest app."""
    return TestApp(app)
