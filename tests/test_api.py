from http import HTTPStatus
from subprocess import Popen
from typing import Dict

import pytest
from webtest import TestApp
from webtest.response import TestResponse

# test bad URLs
# test different HTTP methods, including invalid ones
# test HTTP-level caching (eg with a 30x)
# test https
# test different media types
# test gzip compression

# TODO: Lots of useless warnings

pytestmark = [pytest.mark.usefixtures("sockpuppet_server")]


def test_server_process_running(sockpuppet_server: Popen):
    assert sockpuppet_server.returncode is None


@pytest.mark.parametrize("url,method,expected_status", [
    ("/", "GET", HTTPStatus.NOT_FOUND),
    ("/", "get", HTTPStatus.NOT_FOUND),
    ("/", "gEt", HTTPStatus.NOT_FOUND),
    ("", "GET", HTTPStatus.NOT_FOUND),
    ("/", "POST", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/", "PUT", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/", "DELETE", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/", "PATCH", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/", "dsafaee", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/", "OPTION", HTTPStatus.METHOD_NOT_ALLOWED),
    ("/api", "GET", HTTPStatus.NOT_FOUND),
    ("/api/0", "GET", HTTPStatus.NOT_FOUND),
    ("/api/1", "GET", HTTPStatus.NOT_FOUND),
    ("/api/0/", "GET", HTTPStatus.NOT_FOUND),
    ("/api/1/", "GET", HTTPStatus.NOT_FOUND),
])
def test_request(testapp: TestApp, url: str, method: str, expected_status: HTTPStatus):
    response = testapp.request(url, method=method, expect_errors=True)  # type: TestResponse

    assert response.status_code == expected_status
    assert 'json' in response.content_type
    assert isinstance(response.json, Dict)
    assert len(response.json) > 0

# TODO: Split this into a few parametrized tests (e.g. "trailing slash", "only head and get allowed")
