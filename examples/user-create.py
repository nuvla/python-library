#!/usr/bin/env python3

from nuvla.api import Api as Nuvla
from nuvla.api.resources.user import User


email = "valid@email"
password = "Saf8pass#"  # must contain uppercase letter, number and symbol.

template = {
    "template": {
        "href": "user-template/email-password",
        "email": email,
        "password": password
    }
}

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

# Create Nuvla API handler for User resource.
user_api = User(nuvla)

# Request creation of a new user.
user_id = user_api.create(template)

print(f'New user created: {user_id}')
print(f'Follow instructions in validation email that was sent to {email}.')
