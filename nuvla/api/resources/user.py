
from requests.exceptions import HTTPError

from .base import ResourceBase
from ..api import NuvlaError


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

        return response.json().get('resource-id')

    def logout(self):
        self.nuvla.logout()
