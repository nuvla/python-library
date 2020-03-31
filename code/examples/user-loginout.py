#!/usr/bin/env python3

from nuvla.api import Api as Nuvla, NuvlaError
from nuvla.api.resources.user import User

email = "konstan+gssc2@sixsq.com"
passwd = "Saf8pass%"

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

# Create Nuvla API handler for User resource.
user_api = User(nuvla)

# Login using username (which is user's email) and password.
try:
    # User session resource ID as string is returned.
    session = user_api.login_password(email, passwd)
    print('user session:', session)
except NuvlaError as ex:
    print("Failed authenticating with Nuvla: {}".format(ex.reason))
    # requests.Response
    print(ex.response)
except Exception as ex:
    # Some other error occurred, eg. requests.exceptions.ConnectTimeout
    print("Login to Nuvla failed: {}".format(ex))

# Logs out the user.
user_api.logout()
