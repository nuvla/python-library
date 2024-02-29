
from nuvla.api import Api as Nuvla
from nuvla.api.resources.credential import CredentialK8s, KubeConfig
from .base import ResourceBase

"""
Parent/child hierarchy of the infrastructure service related resources.
 
infrastructure-service-group (no type)
 \_ infrastructure-service (Docker, K8s, S3, Docker Registry)
    \_ (infrastructure service) credential (Docker, K8s, S3, Docker Registry)
"""


class InfraServiceGroup(ResourceBase):
    resource = 'infrastructure-service-group'

    def create(self, name, description=None) -> str:
        return self.add({'name': name,
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

    def create_from_config(self, config_fn, group_id, context=None, name=None, description=None):
        """Create Kubernetes IS and the corresponding credential from
        Kubernetes client `config_fn` file. `group_id` is the ID of the IS group
        to add the IS. If `context` is not provided, the 'current-context' from
        the `config_fn` is used.
        """
        kube = KubeConfig()
        conf = kube.from_file(config_fn)
        if not context:
            context = conf.get('current-context')
        if not context:
            raise Exception('K8s: Context must be provided or set in config.')

        cluster_name, _ = kube.get_cluster_and_user(conf, context)
        if not cluster_name:
            raise Exception(f'K8s: failed to find cluster in context {context}.')

        cluster_url = kube.get_cluster_endpoint(conf, cluster_name)
        if not name:
            name = cluster_name
        infra_id = self.create(cluster_url, group_id, name, description)

        cred = CredentialK8s(self.nuvla)
        isc_id = cred.create_from_config(config_fn, infra_id, context, name, description)
        return infra_id, isc_id


class InfraServiceDocker(InfraService):
    subtype = 'swarm'


class InfraServiceS3(InfraService):
    subtype = 's3'


class InfraServiceRegistry(InfraService):
    subtype = 'registry'
