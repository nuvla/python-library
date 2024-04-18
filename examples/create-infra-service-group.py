#!/usr/bin/env python3

from nuvla.api import Api as Nuvla
from nuvla.api.resources.infra_service import InfraServiceGroup
from nuvla.api.resources.user import User
from utils import nuvla_conf_user_pass


# Set to True to print Nuvla request / response messages to stdout.
debug = False

# Get username and password from configuration file.
username, password = nuvla_conf_user_pass()

# Create Nuvla client. No authentication required.
# nuvla = Nuvla(debug=debug)
nuvla = Nuvla(endpoint='https://localhost', insecure=True, debug=debug)

#
# Login to Nuvla.
#
user_api = User(nuvla)
user_api.login_password(username, password)


#
# Infrastructure service group API object.
#
isg_api = InfraServiceGroup(nuvla)


# Infrastructure services (created later) will set the infrastructure service
# group ID as their parent to indicate they are part of the same group.

#
# Add infrastructure service group.
#
infra_group_id = isg_api.create("Infra service group")
print('infra service group:', infra_group_id)


#
# Add Docker Registry infrastructure service group.
#
registry_group_id = isg_api.create("Docker Registry")
print('infra service registry group:', registry_group_id)

# Logs out the user.
user_api.logout()
