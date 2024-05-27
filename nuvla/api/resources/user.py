
from typing import Tuple
from requests.exceptions import HTTPError

from .base import ResourceBase
from ..api import NuvlaError, Api

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
    
    def _handle_login_response(self, response) -> str:
        try:
            response.raise_for_status()
        except HTTPError as e:
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

        new_nuvla = self.nuvla

        return new_nuvla
    
    def login(self, username_or_key: str, password_or_secret: str) -> Tuple[Api, bool]:
        '''
        Logs in the user.
        :param username_or_key: username or API key
        :param password_or_secret: password or secret
        :return: Api, bool
        If the user is logged in using API key, the second return value is False.
        If the user is logged in using password, the second return value is True.
        '''
        if username_or_key.startswith('credential/'):
            allow_switch_groups = False
            response = self.nuvla.login_apikey(username_or_key, password_or_secret)
        else:
            response = self.nuvla.login_password(username_or_key, password_or_secret)
            allow_switch_groups = True

        return self._handle_login_response(response), allow_switch_groups

    def login_password(self, username: str, password: str) -> Api:
        '''
        Logs in the user using password.
        :param username: username
        :param password: password
        :return: Api
        '''
        response = self.nuvla.login_password(username, password)
        
        return self._handle_login_response(response)

    def login_api(self, api_key: str, secret: str) -> Api:
        '''
        Logs in the user using API key.
        :param api_key: API key
        :param secret: secret
        :return: Api
        '''
        response = self.nuvla.login_apikey(api_key, secret)

        return self._handle_login_response(response)

    def logout(self):
        self.nuvla.logout()

    def switch_user_group(self, group_id: str) -> Api:
        """
        Switches the user group.
        :param group_id: group id (group/<group name>)
        :return: Api
        """
        cimi_collection = self.nuvla.search('session')
        if not cimi_collection.resources:
            raise Exception('No session found.')
        session = cimi_collection.resources[0]
        data = {'claim': group_id}
        self.nuvla.operation(session, 'switch-group', data)
        return self.nuvla