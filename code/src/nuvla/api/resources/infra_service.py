
import os
import base64

import yaml

from nuvla.api import Api as Nuvla
from nuvla.api.resources.credential import CredentialK8s
from . import ResourceBase

"""
Parent/child hierarchy of the infrastructure service related resources.
 
infrastructure-service-group (no type)
 \_ infrastructure-service (Docker, K8s, S3, Docker Registry)
    \_ (infrastructure service) credential (Docker, K8s, S3, Docker Registry)
"""


class InfraServiceGroup(ResourceBase):
    resource = 'infrastructure-service-group'

    def add(self, name, description=None) -> str:
        return super().add({'name': name,
                            'description': description or name})


class InfraService(ResourceBase):
    resource = 'infrastructure-service'
    subtype = None
    infra_service_template = "infrastructure-service-template/generic"

    def __init__(self, nuvla: Nuvla, subtype=None):
        super().__init__(nuvla)
        if not self.subtype and not subtype:
            raise Exception('subtype must be defined.')
        if subtype:
            self.subtype = subtype

    def create(self, endpoint, infra_group_id, name=None, description=None) -> str:
        infra_service = {
            "template": {
                "href": self.infra_service_template,
                "subtype": self.subtype,
                "endpoint": endpoint,
                "name": name or endpoint,
                "description": description or name or endpoint,
                "parent": infra_group_id
            }
        }
        return self.add(infra_service)


class InfraServiceK8s(InfraService):
    subtype = 'kubernetes'

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

    def add_from_config(self, config_fn, group_id, context=None, name=None, description=None):
        """Create Kubernetes IS and the corresponding credential from
        Kubernetes client `config_fn` file. `group_id` is the ID of the IS group
        to add the IS. If `context` is not provided, the 'current-context' from
        the `config_fn` is used.
        """
        conf = self.read_config(config_fn)
        if not context:
            context = conf.get('current-context')
        if not context:
            raise Exception('K8s: Context must be provided or set in config.')

        cluster_name, user_name = self.get_cluster_and_user(conf, context)
        if not cluster_name and not user_name:
            raise Exception(f'K8s: failed to find cluster or user '
                            f'in context {context}.')

        cluster_url = self.get_cluster_endpoint(conf, cluster_name)
        cluster_ca_pem = self.get_cluster_cacert(conf, cluster_name)
        if not cluster_url and not cluster_ca_pem:
            raise Exception(f'K8s: failed to find cluster URL or CA data '
                            f'for cluster {cluster_name}.')

        user_cert, user_key = self.get_client_creds(conf, user_name)
        if not user_cert and not user_key:
            raise Exception(f'K8s: failed to find user cert and key for '
                            f'user {user_name}')

        if not name:
            name = cluster_name
        is_id = self.create(cluster_url, group_id, name, description or name)

        cred = CredentialK8s(self.nuvla)
        isc_id = cred.create(cluster_ca_pem, user_cert, user_key, is_id, name)
        return is_id, isc_id


class InfraServiceDocker(InfraService):
    subtype = 'docker'


class InfraServiceS3(InfraService):
    subtype = 's3'


class InfraServiceRegistry(InfraService):
    subtype = 'registry'


class InfraServiceCred(ResourceBase):
    resource = 'credential'
    subtype = None

    def __init__(self, nuvla: Nuvla, subtype=None):
        super().__init__(nuvla)
        if not self.subtype and not subtype:
            raise Exception('subtype must be defined.')
        if subtype:
            self.subtype = subtype

    def create(self, ):
        pass

    def create_from_config(self, filename, context):
        pass

    def id_by_name(self, name, filter=None) -> list:
        return super().id_by_name(name, filter=f"subtype='{self.subtype}'")


class InfraServiceCredK8s(InfraServiceCred):
    subtype = 'infrastructure-service-swarm'