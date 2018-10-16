from collections import namedtuple
from http import HTTPStatus
from subprocess import Popen
from typing import Dict, Sequence, Tuple

import pytest
import simplejson
import werkzeug
from jsonrpc.exceptions import JSONRPCParseError
from simplejson import JSONDecodeError
from webtest import TestApp, TestRequest, TestResponse

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

Request = namedtuple("Request", ["url", "kwargs", "expected_status"], defaults=["", "", HTTPStatus.OK])
# TODO: expected_jsonrpc_code
# TODO: Make request objects the parameters

GOOD_GETS = (
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        {"method": "GET"}
    ), id="one-valid-user"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,ElaineDiMasi",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="two-valid-users"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdslfsda",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="one-invalid-user"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdsd,ajvaslfsda",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="two-invalid-users"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="one-banned-user"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,puredavie",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="two-banned-users"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,sadfrafdsd",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="banned-invalid"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,sadfrafdsd,JesseT_G",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="banned-invalid-valid"),
    pytest.param(Request(
        "/api/1/user?ids=TEN_GOP,JesseT_G",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="banned-valid"),
    pytest.param(Request(
        "/api/1/user?ids=sadfrafdsd,JesseT_G",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="invalid-valid"),
    pytest.param(Request(
        "/api/1/user?ids=2048",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="invalid-user-id"),
    pytest.param(Request(
        "/api/1/user?ids=@2048",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="numeric-username"),
    pytest.param(Request(
        "/api/1/user?ids=@JesseT_G",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="@-prefix"),
    pytest.param(Request(
        "/api/1/user?ids=18105480",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="valid-numeric-id"),
    pytest.param(Request(
        "/api/1/user?ids=18105480,JesseT_G",
        {"method": "GET"},
        HTTPStatus.OK
    ), id="id-name"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        {"method": "get"},
        HTTPStatus.OK
    ), id="lowercase-method"),
)

BAD_GETS = (
    pytest.param(Request(
        "/api/1/user",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="no-ids"),
    pytest.param(Request(
        "/api/1/user?ids",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-ids"),
    pytest.param(Request(
        "/api/1/user?ids=",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-ids-with-="),
    pytest.param(Request(
        "/api/1/user?ids=,",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-name"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-name-at-end"),
    pytest.param(Request(
        "/api/1/user?ids=,JesseT_G",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-name-at-start"),
    pytest.param(Request(
        "/api/1/user?ids=,,,,",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="many-blanks"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G,,ElaineDiMasi",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="empty-name-in-middle"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        {"method": "fgsfds"},
        HTTPStatus.METHOD_NOT_ALLOWED
    ), id="invalid-method"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        {"method": "PATCH"},
        HTTPStatus.METHOD_NOT_ALLOWED
    ), id="unsupported-method"),

    pytest.param(Request(
        "/api/1/user?ids=JesseT_G    ",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="spaces-at-end"),
    pytest.param(Request(
        "/api/1/user?ids=    JesseT_G",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="spaces-at-start"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G&unknown_parameter",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="unknown-parameter"),
    pytest.param(Request(
        "/api/1/user?ids=JesseT_G",
        {
            "method": "GET",
            "accept": "text/html"
        },
        HTTPStatus.NOT_ACCEPTABLE
    ), id="wont-accept-json"),
    pytest.param(Request(
        f"/api/1/user?ids={'f,' * 6000}f",
        {"method": "GET"},
        HTTPStatus.REQUEST_URI_TOO_LONG
    ), id="large-url"),
    pytest.param(Request(
        "/api/1/user?ids=\0\0\0\0\0\0\0\0",
        {"method": "GET"},
        HTTPStatus.BAD_REQUEST
    ), id="invalid-bytes"),
)

GOOD_POSTS = (
    pytest.param(Request(
        "/api/1/user",
        {
            "method": "POST",
            "content_type": "application/json",
            "json": {
                "jsonrpc": "2.0",
                "id": 689,
                "method": "guess",
                "params": {
                    "ids": ["JesseT_G"]
                }
            }
        },
        HTTPStatus.OK
    ), id="valid-post"),
)

BAD_POSTS = (
    pytest.param(Request(
        "/api/1/user",
        {
            "method": "POST",
            "content_type": "application/json",
            "body": b"sdaafrrrfgtyfe"
        },
        HTTPStatus.BAD_REQUEST
    ), id="garbage-post"),
    pytest.param(Request(
        "/api/1/user",
        {
            "method": "POST",
            "json": {
                "jsonrpc": "2.0",
                "id": 689,
                "method": "guess",
                "params": {
                    "ids": ["JesseT_G"]
                }
            }
        },
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    ), id="valid-post-no-content-type"),
    pytest.param(Request(
        "/api/1/user",
        {
            "method": "POST",
            "content_type": "text/plain",
            "text": "hey what's up all?"
        },
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    ), id="wrong-content-type"),
    # TODO: @ in middle of name
    # TODO: @ at end of name
    # TODO: @ and # in name
    # TODO: Name made only of @ and/or #
    # TODO: # at start of name
    # TODO: # in middle of name
    # TODO: # at end of name
    # TODO: JSON-RPC tests
    #     # TODO: Test HEAD and OPTIONS requests
    #     # TODO: Test the ids=A&ids=B&ids=C form
)

RequestResponse = namedtuple(
    "RequestResponse",
    ["request", "response", "expected_http_status", "expected_jsonrpc_status"]
)


@pytest.fixture(scope="session", params=[*GOOD_GETS, *BAD_GETS, *GOOD_POSTS, *BAD_POSTS])
def request_response(request, testapp: TestApp) -> RequestResponse:
    req = request.param  # type: Request

    test_request = TestRequest.blank(req.url, **req.kwargs)
    test_response = testapp.request(test_request, expect_errors=True)
    return RequestResponse(test_request, test_response, req.expected_status, None)


def test_response_status(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response
    assert response.status_code == request_response.expected_http_status


def test_response_content_type(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response
    assert response.content_type == "application/json"


def test_response_is_dict(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response
    assert isinstance(response.json, Dict)


def test_response_not_empty(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response
    assert len(response.json) > 0


def test_response_apiversion_field(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response
    assert 'jsonrpc' in response.json
    assert response.json['jsonrpc'] == "2.0"


def test_response_id(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response  # type: TestResponse
    request = request_response.request  # type: TestRequest
    expected_jsonrpc_status = request_response.expected_jsonrpc_status  # type: int

    assert "id" in response.json
    response_id = response.json["id"]

    if response.status_code == HTTPStatus.OK:
        assert isinstance(response_id, int)

        if request.method == "POST":
            request_id = request.json["id"]
            assert request_id == response_id
    else:
        if expected_jsonrpc_status == JSONRPCParseError.CODE:
            assert response_id is None

        if request.method == "POST":
            try:
                json = response.json
                if "id" not in json:
                    # Input never gave an "id" field
                    assert response_id is None
            except JSONDecodeError:
                # Input body is not valid JSON
                assert response_id is None


def test_result_provided(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response

    if response.status_code == HTTPStatus.OK:
        assert "result" in response.json
        assert "error" not in response.json

        result = response.json["result"]
        assert isinstance(result, list)
        for r in result:
            assert isinstance(r, dict)
            assert "status" in r
            assert isinstance(r["status"], str)

            assert "id" in r
            assert isinstance(r["id"], str)
            # TODO: Ensure this ID was in the original request, but for POST

            assert "type" in r
            assert isinstance(r["type"], str)
            assert r["type"] == "user"
    else:
        assert "result" not in response.json


def test_error_provided(testapp: TestApp, request_response: RequestResponse):
    response = request_response.response

    if response.status_code != HTTPStatus.OK:
        # TODO: Test for invalid or undetectable id, return id of None
        assert "error" in response.json
        assert "result" not in response.json

        error = response.json["error"]
        assert "code" in error
        code = error["code"]
        assert isinstance(code, int)

        assert "message" in error
        message = error["message"]
        assert isinstance(message, str)
        assert len(message) > 0
    else:
        assert "error" not in response.json


# @pytest.mark.skip
# def test_error_provided(testapp: TestApp, user_request: Tuple[TestResponse, HTTPStatus]):
#     pass

# def test_gzip_request(testapp: TestApp):
#     response = testapp.request(f"/api/1/user?ids=JesseT_G", method="GET", expect_errors=True)  # type: TestResponse
