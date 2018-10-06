# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import csv
import os
import subprocess
import sys
import time
from typing import Callable, Dict, Sequence, Union
import zmq
from zmq import Context, Socket

import pytest
from flask import Flask
from pytest import Item, Session
from webtest import TestApp

import socklint
from sockpuppet.app import create_app
from sockpuppet.settings import TestConfig

from .marks import *

# must write fixtures to fake some mashape headers
pytest_plugins = 'pytester'


def pytest_report_header(config, startdir):

    return (
        f"socklint: {socklint.__file__}",
    )


@pytest.fixture(scope="session")
def app() -> Flask:
    """An application for the tests."""
    _app = create_app(TestConfig)
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

    env["SOCKPUPPET_TRAINED_MODEL_PATH"] = TestConfig.SOCKPUPPET_TRAINED_MODEL_PATH
    env["SOCKPUPPET_WORD_EMBEDDING_PATH"] = TestConfig.SOCKPUPPET_WORD_EMBEDDING_PATH
    env["SOCKPUPPET_SERVER_BIND_ADDRESS"] = TestConfig.SOCKPUPPET_HOST

    context = Context.instance()  # type: Context
    socket = context.socket(zmq.REQ)  # type: Socket
    socket.heartbeat_ivl = 2000
    socket.heartbeat_timeout = 2000
    socket.connect(TestConfig.SOCKPUPPET_HOST)
    process = subprocess.Popen(
        (sys.executable, TestConfig.SOCKPUPPET_MAIN_NAME),  # python main.py
        env=env,
        cwd=TestConfig.SOCKPUPPET_DIR,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    socket.send_json([])
    ping = socket.recv_json()
    assert ping == []
    socket.close()

    yield process

    process.terminate()


@pytest.fixture(scope="session")
def testapp(app: Flask):
    """A Webtest app."""
    return TestApp(app)
