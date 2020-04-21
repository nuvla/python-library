
from nuvla.api import Api as Nuvla
from . import ResourceBase

"""
Parent/child hierarchy of the infrastructure service related resources.
 
infrastructure-service-group (no type)
 \_ infrastructure-service (Docker, K8s, S3, Docker Registry)
    \_ (infrastructre service) credential (Docker, K8s, S3, Docker Registry)
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

    def add(self, endpoint, infra_group_id, name=None, description=None) -> str:
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
        return super().add(infra_service)


class InfraServiceK8s(InfraService):
    subtype = 'kubernetes'


class InfraServiceDocker(InfraService):
    subtype = 'docker'


class InfraServiceS3(InfraService):
    subtype = 'S3'


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