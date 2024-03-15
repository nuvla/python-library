#!/usr/bin/env python3

from nuvla.api import Api as Nuvla
from nuvla.api.resources.infra_service import (InfraServiceK8s,
                                               InfraServiceS3,
                                               InfraServiceRegistry)
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


# Infrastructure services set infra service group ID as their parent to indicate
# they are part of the same group.

infra_group = 'infrastructure-service-group/3c8d8360-508e-47b1-8196-7b0e859c6be4'

#
# Creates infrastructure service records for K8s and S3 and adds them to the
# common infrastructure service group.
#

#
# Kubernetes infrastructure service.
#
is_k8s = InfraServiceK8s(nuvla)
infra_k8s_id = is_k8s.create('https://k8s.local', infra_group, 'K8s cluster')
print('Kubernetes:', infra_k8s_id)

#
# S3 infrastructure service.
#
is_s3 = InfraServiceS3(nuvla)
infra_s3_id = is_s3.create('https://s3.local', infra_group, 'S3')
print('S3:', infra_k8s_id)

#
# Creates infrastructure service record for private Docker Registry and adds it
# the infrastructure service group.
#
infra_group_registry = 'infrastructure-service-group/1af011e0-d496-4fe8-a00b-b781aebe4813'
is_registry = InfraServiceRegistry(nuvla)
infra_registry = is_registry.create('https://private.registry',
                                    infra_group_registry, 'Private Registry')
print('Docker registry:', infra_registry)

# Logs out the user.
user_api.logout()
