from copy import copy

from requests import Response
from requests.exceptions import HTTPError

from .base import ResourceBase
from ..api import NuvlaError, Api


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

    def __init__(self, nuvla: Api):
        super().__init__(nuvla)

        self._can_switch_groups = False

    def create(self, template: dict) -> str:
        """
        Creates new user according to provided template. Returns new user ID or
        throws an exception.
        :param template:
        :return: string
        """
        return self.add(template)
    
    def login(self, username_or_key: str, password_or_secret: str) -> Api:
        """
        Logs in the user and returns the Nuvla client.

        If the user is logged in using API key.
        If the user is logged in using password, the second return value is True.

        :param username_or_key: username or API key
        :param password_or_secret: password or secret
        :return: Api
        """

        if username_or_key.startswith('credential/'):
            return self.login_apikey(username_or_key, password_or_secret)
        else:
            return self.login_password(username_or_key, password_or_secret)

    def login_password(self, username: str, password: str) -> Api:
        """
        Logs in the user using password and returns the Nuvla client.
        :param username: username
        :param password: password
        :return: Api
        """
        response = self.nuvla.login_password(username, password)

        handle_response(response)

        self._can_switch_groups = True

        return copy(self.nuvla)

    def login_apikey(self, api_key: str, secret: str) -> Api:
        """
        Logs in the user using API key and returns the Nuvla client.
        :param api_key: API key
        :param secret: secret
        :return: Api
        """
        response = self.nuvla.login_apikey(api_key, secret)

        handle_response(response)

        self._can_switch_groups = False

        return copy(self.nuvla)

    def logout(self):
        self.nuvla.logout()

    def current_session_id(self) -> str:
        """
        Returns the current session ID.
        :return: string
        """
        return self.nuvla.current_session()

    def current_session(self) -> dict:
        """
        Returns the current session.
        :return: dict
        """
        resource_type = 'session'
        sessions = self.nuvla.search(resource_type)
        if not sessions.resources:
            raise Exception('No session found.')
        return sessions.resources[0].data

    def can_switch_groups(self) -> bool:
        """
        Returns True if the user can switch groups, False otherwise.
        :return: bool
        """
        return self._can_switch_groups

    def switch_group(self, group_id: str) -> Api:
        """
        Switches the user group and returns the updated Nuvla client.
        :param group_id: group id (group/<group name>)
        :return: Api
        """
        cimi_collection = self.nuvla.search('session')
        if not cimi_collection.resources:
            raise Exception('No session found.')
        session = cimi_collection.resources[0]
        data = {'claim': group_id}
        self.nuvla.operation(session, 'switch-group', data)
        return copy(self.nuvla)
