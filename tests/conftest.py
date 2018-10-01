# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import csv
import sys
import time
from typing import Callable, Dict, Sequence, Union

import pandas
import pytest
from pandas import DataFrame
from pytest import Item, Session
from webtest import TestApp

from sockpuppet.app import create_app
from sockpuppet.database import db as _db
from sockpuppet.settings import TestConfig

from .marks import *


def pytest_collection_modifyitems(session, config, items: Sequence[Item]):
    to_remove = set()
    for item in items:
        modes = item.get_closest_marker("modes")
        if modes is not None:
            # If we're explicitly using a subset of modes...
            if hasattr(item, "callspec") and hasattr(item.callspec, "params"):
                params = item.callspec.params
                if "mode" in params and params["mode"] not in modes.args:
                    # If this mode isn't in the list...
                    to_remove.add(item)

    for i in to_remove:
        items.remove(i)


@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def user(db):
    """A user for the tests."""
    user = UserFactory(password='myprecious')
    db.session.commit()
    return user
