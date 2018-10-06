from http import HTTPStatus


class EmptyNameError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

        self.code = HTTPStatus.BAD_REQUEST
        self.message = "Usernames must not be empty"
