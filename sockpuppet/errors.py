from http import HTTPStatus
from typing import Dict, Optional

from flask import jsonify


class SockPuppetError(Exception):
    def __init__(self, status_code: HTTPStatus, message: str, payload: Dict=None):
        Exception.__init__(self, message)
        self.message = message
        self.status_code = status_code  # type: HTTPStatus
        self.payload = payload

    def for_json(self) -> str:
        return self.message


class EmptyNameError(SockPuppetError):
    def __init__(self):
        SockPuppetError.__init__(self, HTTPStatus.BAD_REQUEST, "Usernames must not be empty")


class BadCharacterError(SockPuppetError):
    def __init__(self):
        SockPuppetError.__init__(self, HTTPStatus.BAD_REQUEST, "Usernames must be made of printable characters")
