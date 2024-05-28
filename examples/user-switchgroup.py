#!/usr/bin/env python3

from nuvla.api import Api as Nuvla, NuvlaError
from nuvla.api.resources.user import User

# Must be valid email address.
username = '<email@example.com>'
# Must contain uppercase letter, number and symbol.
password = ''

# User group to switch to. Must start with 'group/'.
user_group = 'group/<your group>'

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

# Create Nuvla API handler for User resource.
user_api = User(nuvla)

# Login using username (which is user's email) and password.
session = user_api.login_password(username, password)
print('user session:', session)

# Switches the user group.
nuvla = user_api.switch_group('group/sixsq-dev')

# Now you can use the Nuvla client 'nuvla' to perform
# operations as the user in the new group.

# Logs out the user.
user_api.logout()
