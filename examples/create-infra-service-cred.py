#!/usr/bin/env python3

import yaml
from pprint import pprint

from nuvla.api import Api as Nuvla
from nuvla.api.resources.credential import (CredentialK8s,
                                            CredentialS3,
                                            CredentialDockerRegistry)
from utils import nuvla_conf_user_pass


username, password = nuvla_conf_user_pass()

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)


userpass = {"href" : "session-template/password",
         "username" : username,
         "password" : password
         }
nuvla.login(userpass)

# Fake infra service ID to which all credentials will be attached.
infra_service_id = "infrastructure-service/1-2-3-4-5"

#
# Kubernetes credentials.
#
cred_k8s = CredentialK8s(nuvla)

# Add credentials directly or from a Kubernetes client config file.

## CA certificate.
#ca = "-----BEGIN CERTIFICATE----- ...",
## User certificate.
#cert = "-----BEGIN CERTIFICATE----- ...",
## User key.
#key = "-----BEGIN RSA PRIVATE KEY----- ..."
#
#k8s_cred_id = cred_k8s.create(ca, cert, key, infra_service_id, "My K8s creds")

def read_yaml_file(filepath):
    with open(filepath, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

config = read_yaml_file('data/example-k8s-config.yaml')
print(config)

k8s_cred_id = cred_k8s \
    .create_from_config(config, infra_service_id,
                        context='first-k8s-cluster-user', name='My K8s creds')
print('Kubernetes creds: ', k8s_cred_id)

#
# S3 credentials.
#
key = "AKI..."
secret = "SECRET..."
s3_cred = CredentialS3(nuvla)
s3_cred_id = s3_cred.create(key, secret, infra_service_id, "My S3 creds")
print('S3 creds: ', s3_cred_id)

#
# Docker registry credentials.
#
username = 'username'
password = 'password'
dr_cred = CredentialDockerRegistry(nuvla)
dr_cred_id = dr_cred.create(username, password, infra_service_id, "My Registry creds")
print('Docker Registry creds: ', dr_cred_id)

# Logs out the user.
nuvla.logout()
