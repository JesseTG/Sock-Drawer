from http import HTTPStatus
from subprocess import Popen
from typing import Dict, Sequence, Tuple
from collections import namedtuple

import pytest
from webtest import TestApp
from webtest.response import TestResponse

pytestmark = [pytest.mark.usefixtures("sockpuppet_server")]

# test url parameters
# test responses
# test user caching
# test handling of errors:
#  - redis not available
#  - sock puppet not available

# test query by invalid id
# test query by banned id
# test query by multiple invalid ids
# test query multiple banned ids
# test query mix of valid, invalid, and banned ids
# test all-numeric usernames

Request = namedtuple("Request", ["url", "expected_status", "kwargs"])

REQUESTS = (
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="one-valid-user"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,ElaineDiMasi",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="two-valid-users"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdsdajvaslfsda",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="one-invalid-user"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdsd,ajvaslfsda",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="two-invalid-users"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="one-banned-user"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,puredavie",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="two-banned-users"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,sadfrafdsd",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="banned-invalid"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,sadfrafdsd,JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="banned-invalid-valid"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="banned-valid"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdsd,JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="invalid-valid"),
    pytest.param(Request(
        "/api/1/user?ids=2048",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="invalid-user-id"),
    pytest.param(Request(
        "/api/1/user?ids=@2048",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="numeric-username"),
    pytest.param(Request(
        "/api/1/user?ids=@JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="@-prefix"),
    pytest.param(Request(
        "/api/1/user?ids=18105480",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="valid-numeric-id"),
    pytest.param(Request(
        "/api/1/user?ids=18105480,JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="id-name"),
    pytest.param(Request(
        "/api/1/user",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="no-ids"),
    pytest.param(Request(
        "/api/1/user?ids",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-ids"),
    pytest.param(Request(
        "/api/1/user?ids=",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-ids-with-="),
    pytest.param(Request(
        "/api/1/user?ids=,",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-name"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-name-at-end"),
    pytest.param(Request(
        "/api/1/user?ids=,JesseT_G",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-name-at-start"),
    pytest.param(Request(
        "/api/1/user?ids=,,,,",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="many-blanks"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,,ElaineDiMasi",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="empty-name-in-middle"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        HTTPStatus.METHOD_NOT_ALLOWED,
        {"method": "fgsfds"}
    ), id="invalid-method"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        HTTPStatus.METHOD_NOT_ALLOWED,
        {"method": "POST"}
    ), id="unsupported-method"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        HTTPStatus.OK,
        {"method": "get"}
    ), id="lowercase-method"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G    ",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="spaces-at-end"),
    pytest.param(Request(
        "/api/1/user?ids=    JesseT_G",
        HTTPStatus.OK,
        {"method": "GET"}
    ), id="spaces-at-start"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G&unknown_parameter",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="unknown-parameter"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        HTTPStatus.NOT_ACCEPTABLE,
        {
            "method": "GET",
            "accept": "text/html"
        }
    ), id="wont-accept-json"),
    pytest.param(Request(
        f"/api/1/user?ids={'f' * 6000}",
        HTTPStatus.REQUEST_URI_TOO_LONG,
        {"method": "GET"}
    ), id="large-url"),
    pytest.param(Request(
        "/api/1/user?ids=\0\0\0\0\0\0\0\0",
        HTTPStatus.BAD_REQUEST,
        {"method": "GET"}
    ), id="invalid-bytes"),
    # TODO: @ in middle of name
    # TODO: @ at end of name
    # TODO: @ and # in name
    # TODO: Name made only of @ and/or #
    # TODO: # at start of name
    # TODO: # in middle of name
    # TODO: # at end of name
)


# @pytest.fixture(scope="session", params=[
#     # TODO: Test HEAD and OPTIONS requests
#     # TODO: Test the ids=A&ids=B&ids=C form
# ])
@pytest.fixture(scope="session", params=REQUESTS)
def user_request(request, testapp: TestApp) -> Tuple[TestResponse, HTTPStatus]:
    req = request.param  # type: Request
    return testapp.request(req.url, expect_errors=True, **req.kwargs), req.expected_status


def test_response_status(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse
    expected_status = user_request[1]  # type: HTTPStatus

    assert response.status_code == expected_status


def test_response_content_type(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse

    assert 'json' in response.content_type
    assert 'html' not in response.content_type
    assert isinstance(response.json, Dict)


def test_response_not_empty(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse

    assert len(response.json) > 0


def test_response_apiversion_field(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse

    assert 'apiVersion' in response.json


def test_guesses_provided(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse
    expected_status = user_request[1]  # type: HTTPStatus

    if expected_status == HTTPStatus.OK:
        assert "guesses" in response.json
        guesses = response.json["guesses"]
        assert isinstance(guesses, list)

        for g in guesses:
            assert isinstance(g, dict)
            assert "status" in g
            assert isinstance(g["status"], str)

            assert "id" in g
            assert isinstance(g["id"], str)

            assert "type" in g
            assert isinstance(g["type"], str)
            assert g["type"] == "user"

            if g["status"] == "OK":
                assert "bot" in g
                assert isinstance(g["bot"], bool)
            else:
                assert "message" in g
                assert isinstance(g["message"], str)
    else:
        assert "guesses" not in response.json


def test_status_provided(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse

    assert "status" in response.json
    assert isinstance(response.json["status"], int)

    assert "statusType" in response.json
    assert isinstance(response.json["statusType"], str)


def test_message_provided(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
    response = user_request[0]  # type: TestResponse

    assert "message" in response.json
    assert isinstance(response.json["message"], str)

# def test_gzip_request(testapp: TestApp):
#     response = testapp.request(f"/api/1/user?ids=JesseT_G", method="GET", expect_errors=True)  # type: TestResponse
