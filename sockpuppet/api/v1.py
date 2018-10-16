from collections import namedtuple
from enum import Enum
from http import HTTPStatus
from json import JSONEncoder
from random import randint
from typing import Sequence, Union
import connexion

import flask
import zmq
from flask import Blueprint, Flask, Response, Request, current_app, jsonify
from flask_restful import Resource, fields, inputs, reqparse
from twint import Config
from twitter_scraper import get_tweets
from werkzeug.exceptions import BadRequest, HTTPException
from werkzeug.datastructures import MIMEAccept
from jsonrpc.exceptions import JSONRPCInvalidParams, JSONRPCInternalError
from connexion.exceptions import ProblemException

from sockpuppet.errors import BadCharacterError, EmptyNameError, SockPuppetError
from sockpuppet.extensions import cache, zmq_socket

Guess = namedtuple("Guess", ["status", "type", "id", ])
# TODO: Subclass namedtuple


BOT = "bot"
HUMAN = "human"
UNKNOWN = "unknown"
UNAVAILABLE = "unavailable"
# TODO: Use an Enum


def user_or_id(name: str) -> Union[str, int]:
    # TODO: Validate with a proper regex
    if name.isdigit():
        # If this is a user ID...
        return int(name)
    else:
        # Return the original username, sans any @'s
        return name.replace("@", "")
        # Prefix an all-digit username with @ to treat it as a name, not an id


def parse_tweet_ids(arg: str) -> Sequence[int]:
    return tuple(map(inputs.positive, arg.split(',')))


def get_recent_tweets(user: str, limit: int) -> Sequence[str]:

    tweets = tuple(t for t in get_tweets(user, pages=1))
    result = tuple(t["text"] for t in tweets)
    # TODO: Doesn't distinguish between screen name and user id

    return result

# try getting tweets with twint first, then with twarc
# twint uses web scraping, so no api limits but it can break
# use twarc for more stability
# cache tweets aggressively

# For each username:
#   - Get 20 recent tweets
#   - If a majority of them are bot-like, report them as a bot


def handle_http_exception(rpcerror):
    def _handle(exception: HTTPException):
        response_id = randint(-((2**53) - 1), (2**53) - 1)
        response = {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": {
                "code": rpcerror.CODE,
                "message": rpcerror.MESSAGE,
                "data": str(exception)
            }
        }

        json_response = jsonify(response)  # type: Response
        json_response.status_code = exception.code

        return json_response

    return _handle


def make_guess(ids: Sequence[str], response_id: int) -> Response:
    guesses = []
    request = connexion.request  # type: Request
    app = current_app  # type: Flask
    accept_mimetypes = request.accept_mimetypes
    if len(accept_mimetypes) > 0 and not request.accept_mimetypes.accept_json:
        # If there's no Accept header, assume they'll take JSON...
        # ...but if they provide it and don't...
        query_response = {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": {
                "code": 406,
                "message": "Not Acceptable"
            }
        }
        response = jsonify(query_response)  # type: Response
        response.status_code = HTTPStatus.NOT_ACCEPTABLE
        response.content_type = "application/json"

        return response

    if len(request.url) > app.config["MAX_URL_LENGTH"]:
        # TODO: Move this to BEFORE the URL is actually processed
        query_response = {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": {
                "code": 414,
                "message": "Request URI Too Long"
            }
        }
        response = jsonify(query_response)  # type: Response
        response.status_code = HTTPStatus.REQUEST_URI_TOO_LONG
        response.content_type = "application/json"

        return response

    for i in ids:
        guess = None
        try:
            tweets = get_recent_tweets(i, 20)  # type: Sequence[str]
            sock_request = {
                "jsonrpc": "2.0",
                "id": randint(-((2**53) - 1), (2**53) - 1),
                "method": "guess",
                "params": tweets
            }
            zmq_socket.socket.send_json(sock_request)
            results = zmq_socket.socket.recv_json()  # type: Dict

            # TODO: Check for errors
            # TODO: Conform to the API I designed
            result_array = results["result"]

            guess = Guess(
                id=str(i),
                type="user",
                status=BOT if (sum(result_array) / len(result_array)) >= 0.5 else HUMAN
            )
        except ValueError:
            # The user is private or doesn't exist...
            guess = Guess(
                id=str(i),
                type="user",
                status=UNAVAILABLE
            )

        guesses.append(guess)

    query_response = {
        "jsonrpc": "2.0",
        "id": response_id,
        "result": guesses
    }
    response = jsonify(query_response)  # type: Response

    response.status_code = HTTPStatus.OK
    response.content_type = "application/json"

    return response


def get_user(ids: Sequence[str]) -> Response:
    response_id = randint(-((2**53) - 1), (2**53) - 1)

    return make_guess(ids, response_id)


def post_user() -> Response:
    content_type = connexion.request.headers["Content-Type"]  # type: str
    json = connexion.request.json  # type: Dict
    # TODO: Convert to JSONRPC request
    # TODO: Handle errors

    ids = json["params"]["ids"]
    response_id = json["id"]

    return make_guess(ids, response_id)
