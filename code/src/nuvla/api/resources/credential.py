
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

    @classmethod
    def build_template(cls, cred_data: dict, parent, name, description=None):
        cred = {
            "name": name,
            "description": description or name,
            "template": {
                "href": f"credential-template/{cls.subtype}",
                "parent": parent
            }
        }
        cred['template'].update(cred_data)
        return cred

    def create_from_template(self, cred_data: dict, parent, name, description=None):
        cred = self.build_template(cred_data, parent, name, description)
        return self.add(cred)


class CredentialCOE(Credential):
    def create(self, ca, cert, key, infra_service_id, name, description=None):
        cred_data = {
            "ca": ca,
            "cert": cert,
            "key": key
        }
        return self.create_from_template(cred_data, infra_service_id, name,
                                         description)


class KubeConfig:

    @staticmethod
    def decode(data):
        return base64.b64decode(data).decode()

    @staticmethod
    def from_string(config: str) -> dict:
        return yaml.safe_load(config)

    @classmethod
    def from_file(cls, fname: str) -> dict:
        with open(os.path.expanduser(fname)) as fh:
            config = cls.from_string(fh.read())
        return config

    @staticmethod
    def get_cluster_and_user(config: dict, context_name=None):
        """Use current context if `context_name` is not provided.
        """
        cluster_n = None
        user_n = None
        if not context_name:
            context_name = config.get('current-context')
        for cx in config.get('contexts', []):
            if cx.get('name') == context_name:
                cluster_n = cx.get('context').get('cluster')
                user_n = cx.get('context').get('user')
        return cluster_n, user_n

    @classmethod
    def get_cluster_cacert(cls, config: dict, cluster_name):
        for c in config.get('clusters'):
            if c.get('name') == cluster_name:
                ca = c.get('cluster').get('certificate-authority-data')
                return cls.decode(ca)

    @staticmethod
    def get_cluster_endpoint(config: dict, cluster_name):
        for c in config.get('clusters'):
            if c.get('name') == cluster_name:
                return c.get('cluster').get('server')

    @classmethod
    def get_client_creds(cls, config: dict, user_name):
        cert = None
        key = None
        for u in config.get('users'):
            if u.get('name') == user_name:
                cert = u.get('user').get('client-certificate-data')
                key = u.get('user').get('client-key-data')
        return cls.decode(cert), cls.decode(key)

    @classmethod
    def get_certs(cls, config: dict, context_name=None):
        """Returns CA cert, user cert and key from the requested `context_name`
        or the current context."""
        cluster_name, user_name = \
            cls.get_cluster_and_user(config, context_name=context_name)
        ca_cert = cls.get_cluster_cacert(config, cluster_name)
        user_cert, user_key = cls.get_client_creds(config, user_name)
        return ca_cert, user_cert, user_key


class CredentialK8s(CredentialCOE):

    subtype = 'infrastructure-service-kubernetes'

    def create_from_file(self, filename: str, infra_service_id, context,
                         name=None, description=None):
        return self.create_from_config(KubeConfig().from_file(filename),
                                       infra_service_id, context, name,
                                       description)

    def create_from_config(self, conf: dict, infra_service_id, context,
                           name=None, description=None):
        """Take kubectl `conf` as dict (representation of ~/.kube/conf YAML),
        extract K8s cluster CA and user certs from `context`.
        """
        kube = KubeConfig()
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


class CredentialDockerSwarm(CredentialCOE):

    subtype = 'infrastructure-service-swarm'


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
