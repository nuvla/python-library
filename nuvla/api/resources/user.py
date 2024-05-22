
from requests import Response
from requests.exceptions import HTTPError

from .base import ResourceBase
from ..api import NuvlaError


def handle_HTTPErrorException(e: HTTPError, response: Response):
    try:
        json_msg = e.response.json()
        message = json_msg.get('message')
        if message is None:
            error = json_msg.get('error')
            message = error.get('code') + ' - ' + error.get('reason')
    except:
        try:
            message = e.response.text
        except:
            message = str(e)
    raise NuvlaError(message, response)


def handle_response(response: Response):
    try:
        response.raise_for_status()
    except HTTPError as e:
        handle_HTTPErrorException(e, response)


class User(ResourceBase):
    resource = 'user'

    def create(self, template: dict) -> str:
        """
        Creates new user according to provided template. Returns new user ID or
        throws an exception.
        :param template:
        :return: string
        """
        return self.add(template)

    def login_password(self, username, password):
        response = self.nuvla.login_password(username, password)

        handle_response(response)

        return response.json().get('resource-id')

    def login_apikey(self, key, secret):
        response = self.nuvla.login_apikey(key, secret)

        handle_response(response)

        return response.json().get('resource-id')

    def logout(self):
        self.nuvla.logout()
