
import os
import base64

import yaml

from .base import ResourceBase
from nuvla.api import Api as Nuvla


class Credential(ResourceBase):

    resource = 'credential'
    subtype = None

    def __init__(self, nuvla: Nuvla, subtype=None):
        super().__init__(nuvla)
        if not self.subtype and not subtype:
            raise Exception('subtype must be defined.')
        if subtype:
            self.subtype = subtype

    def find_parent(self, parent):
        filters = "parent='{}'".format(parent)
        creds = self.nuvla.search(self.resource, filter=filters, select="id")
        return creds.resources

    def id_by_name(self, name, filter=None) -> list:
        return super().id_by_name(name, filter=f"subtype='{self.subtype}'")

    def create_from_template(self, cread_data, parent, name, description=None):
        cred = {
            "name": name,
            "description": description or name,
            "template": {
                "href": f"credential-template/{self.subtype}",
                "parent": parent
            }
        }
        cred['template'].update(cread_data)
        return self.add(cred)


class KubeConfig:

    @staticmethod
    def read_config(fname) -> dict:
        with open(os.path.expanduser(fname)) as fh:
            config = yaml.safe_load(fh.read())
        return config

    @staticmethod
    def get_cluster_and_user(config, context_name):
        cluster_n = None
        user_n = None
        for cx in config.get('contexts', []):
            if cx.get('name') == context_name:
                cluster_n = cx.get('context').get('cluster')
                user_n = cx.get('context').get('user')
        return cluster_n, user_n

    @staticmethod
    def get_cluster_cacert(config, cluster_name):
        for c in config.get('clusters'):
            if c.get('name') == cluster_name:
                ca = c.get('cluster').get('certificate-authority-data')
                return base64.b64decode(ca).decode()

    @staticmethod
    def get_cluster_endpoint(config, cluster_name):
        for c in config.get('clusters'):
            if c.get('name') == cluster_name:
                return c.get('cluster').get('server')

    @staticmethod
    def get_client_creds(config, user_name):
        cert = None
        key = None
        for u in config.get('users'):
            if u.get('name') == user_name:
                cert = u.get('user').get('client-certificate-data')
                key = u.get('user').get('client-key-data')
        return base64.b64decode(cert).decode(), base64.b64decode(key).decode()


class CredentialK8s(Credential):

    subtype = 'infrastructure-service-swarm'

    def create(self, ca, cert, key, infra_service_id, name, description=None):
        cred_data = {
            "ca": ca,
            "cert": cert,
            "key": key
        }
        return self.create_from_template(cred_data, infra_service_id, name,
                                         description)

    def create_from_config(self, filename, infra_service_id, context, name=None,
                           description=None):
        kube = KubeConfig()
        conf = kube.read_config(filename)
        cluster_name, user_name = kube.get_cluster_and_user(conf, context)
        if not cluster_name and not user_name:
            raise Exception(f'K8s: failed to find cluster or user '
                            f'in context {context}.')

        cluster_ca_pem = kube.get_cluster_cacert(conf, cluster_name)
        if not cluster_ca_pem:
            raise Exception(f'K8s: failed to find cluster CA data '
                            f'for cluster {cluster_name}.')

        user_cert, user_key = kube.get_client_creds(conf, user_name)
        if not user_cert and not user_key:
            raise Exception(f'K8s: failed to find user cert and key for '
                            f'user {user_name}')

        return self.create(cluster_ca_pem, user_cert, user_key, infra_service_id,
                           name or cluster_name, description)


class CredentialDockerSwarm(Credential):

    subtype = 'infrastructure-service-swarm'

    def create(self, ca, cert, key, infra_service_id, name, description=None):
        cred_data = {
            "ca": ca,
            "cert": cert,
            "key": key
        }
        return self.create_from_template(cred_data, infra_service_id, name,
                                         description)



class CredentialS3(Credential):

    subtype = 'infrastructure-service-minio'

    def create(self, key, secret, infra_service_id, name, description=None):
        cred_data = {
            "access-key": key,
            "secret-key": secret
        }
        return self.create_from_template(cred_data, infra_service_id, name,
                                         description)


class CredentialDockerRegistry(Credential):

    subtype = 'infrastructure-service-registry'

    def create(self, username, password, infra_service_id, name, description=None):
        cred_data = {
            'username': username,
            'password': password
        }
        return self.create_from_template(cred_data, infra_service_id, name,
                                         description)
