from collections import namedtuple
from typing import Sequence, Union
from json import JSONEncoder
from http import HTTPStatus

from twitter_scraper import get_tweets
from twint import Config
from flask import Blueprint, Flask, current_app
from flask_restful import Resource, reqparse, fields, inputs
from sockpuppet.extensions import cache, zmq_socket
from socklint import Response, Guess
from sockpuppet.errors import EmptyNameError
import zmq

blueprint = Blueprint("api.v1", __name__)


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
        raise EmptyNameError("america")

    id_strings = arg.split(',')

    if any(len(i) == 0 for i in id_strings):
        # If any argument is empty...
        raise EmptyNameError("spain")
        # TODO: How to provide my own result structure?  My own handler?

    return tuple(map(user_or_id, id_strings))


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
    nullable=False,
    required=True,
    # location="args",
    trim=True
)

# TODO: Use https://flask-restful.readthedocs.io/en/latest/extending.html#define-custom-error-messages
# for error handling


class User(Resource):
    def get(self):
        args = user_parser.parse_args(strict=True)
        user_ids = args.ids  # type: Sequence[str]

        guesses = []
        for i in user_ids:
            try:
                tweets = get_recent_tweets(user_ids[0], 20)  # type: Sequence[str]
                zmq_socket.socket.send_json(tweets)
                results = zmq_socket.socket.recv_json()  # type: Sequence[bool]

                guesses.append(Guess(
                    id=str(i),
                    type="user",
                    status="OK",
                    bot=(sum(results) / len(results)) >= 0.5
                ))
            except ValueError:
                # The user is private or doesn't exist...

                guesses.append(Guess(
                    id=str(i),
                    type="user",
                    status="UserNotFound",
                    message="This user is private or doesn't exist"
                ))

        response = Response(guesses=guesses)
        return response, HTTPStatus.OK


class Tweet(Resource):
    def get(self):
        current_app.logger.warning("It me")

        return {
            "results": ["yes"]
        }, 200


class Text(Resource):
    def get(self):
        current_app.logger.warning("It me")

        return {
            "results": ["yes"]
        }, 200
