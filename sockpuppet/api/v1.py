from collections import namedtuple
from typing import Sequence, Union
from json import JSONEncoder
from http import HTTPStatus

import flask
from twitter_scraper import get_tweets
from twint import Config
from flask import Blueprint, Flask, current_app, Response
from flask_restful import Resource, reqparse, fields, inputs
from sockpuppet.extensions import cache, zmq_socket
from sockpuppet.errors import SockPuppetError, EmptyNameError, BadCharacterError
from werkzeug.exceptions import BadRequest, HTTPException
import zmq
from flask import jsonify

API_VERSION = "1.0"
API_VERSION_FIELD = 'apiVersion'

blueprint = Blueprint("api.v1", __name__)


BotQueryResponse = namedtuple("BotQueryResponse", ["apiVersion", "status", "statusType", "message", "guesses"])
Guess = namedtuple("Guess", ["status", "type", "id", "message", "bot"], defaults=["OK", "", "", "", ""])
# TODO: Subclass namedtuple


def handle_error(error: SockPuppetError):
    response = jsonify(BotQueryResponse(
        apiVersion=API_VERSION,
        status=error.status_code,
        statusType=type(error).__name__,
        message=error.message,
        guesses=()
    ))  # type: Response

    response.status_code = error.status_code

    return response


@blueprint.app_errorhandler(HTTPException)
def handle_http_error(error: HTTPException):
    message = error.data["message"]["ids"] if "data" in dir(error) else error.description
    response = jsonify(BotQueryResponse(
        apiVersion=API_VERSION,
        status=error.code,
        statusType=type(error).__name__,
        message=message,
        guesses=()
    ))  # type: Response

    response.status_code = error.code

    return response

for i in (EmptyNameError, BadCharacterError):
    blueprint.register_error_handler(i, handle_error)

# for i in (400, 405):
#     blueprint.register_error_handler(i, handle_http_error)


def user_or_id(name: str) -> Union[str, int]:
    # TODO: Validate with a proper regex
    if name.isdigit():
        # If this is a user ID...
        return int(name)
    else:
        # Return the original username, sans any @'s
        return name.replace("@", "")
        # Prefix an all-digit username with @ to treat it as a name, not an id


def parse_user_ids(arg: str) -> Sequence[str]:
    if arg is None or len(arg) == 0:
        raise EmptyNameError()
    elif not arg.isprintable():
        raise BadCharacterError()

    id_strings = arg.split(',')

    if any(len(i) == 0 for i in id_strings):
        # If any argument is empty...
        raise EmptyNameError()
        # TODO: How to provide my own result structure?  My own handler?

    return tuple(user_or_id(i) for i in id_strings)


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

user_parser = reqparse.RequestParser()
user_parser.add_argument(
    'ids',
    type=parse_user_ids,
    nullable=True,
    required=False,
    # location="args",
    trim=True
)


def get_user():
    args = user_parser.parse_args(strict=True)
    user_ids = args.ids  # type: Sequence[str]

    if not args.ids:
        raise EmptyNameError()

    guesses = []
    for i in user_ids:
        guess = None
        try:
            tweets = get_recent_tweets(user_ids[0], 20)  # type: Sequence[str]
            zmq_socket.socket.send_json(tweets)
            results = zmq_socket.socket.recv_json()  # type: Sequence[bool]

            guess = Guess(
                id=str(i),
                type="user",
                status="OK",
                bot=(sum(results) / len(results)) >= 0.5
            )
        except ValueError:
            # The user is private or doesn't exist...
            guess = Guess(
                id=str(i),
                type="user",
                status="UserNotFound",
                message="This user is private or doesn't exist"
            )

        guesses.append(guess)

    query_response = BotQueryResponse(
        apiVersion=API_VERSION,
        status=HTTPStatus.OK,
        statusType="OK",
        message="Success",
        guesses=guesses
    )
    response = jsonify(query_response)  # type: Response

    response.status_code = HTTPStatus.OK
    response.content_type = "application/json"

    return response


def post_user():
    return "france"
