#!/usr/bin/env python3

from nuvla.api import Api as Nuvla
from nuvla.api.resources.user import User


email = "konstan+gssc2@sixsq.com"

template = {
    "template": {
        "href": "user-template/email-password",
        "email": email,
        # must contain uppercase letter, number and symbol.
        "password": "Saf8pass%"
    }
}

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

# Create Nuvla API handler for User resource.
user_api = User(nuvla)

# Request creation of a new user.
user_id = user_api.create(template)

print('New user created: {}'.format(user_id))
print('Validation email was sent to {}.'.format(email))
