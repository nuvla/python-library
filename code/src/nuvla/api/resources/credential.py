
from .base import ResourceBase


class Credential(ResourceBase):

    resource = 'credential'

    def find_parent(self, parent):
        filters = "parent='{}'".format(parent)
        creds = self.nuvla.search(self.resource, filter=filters, select="id")
        return creds.resources


class CredentialK8s(Credential):

    def create(self, ca, cert, key, infra_service_id, name, description=None):
        cred = {
            "name": name,
            "description": description or name,
            "template": {
                "href": "credential-template/infrastructure-service-swarm",
                "parent": infra_service_id,
                "ca": ca,
                "cert": cert,
                "key": key
            }
        }
        return self.add(cred)


class CredentialS3(Credential):

    def create(self, key, secret, infra_service_id, name, description=None):
        cred = {
            "name": name,
            "description": description or name,
            "template": {
                "href": "credential-template/infrastructure-service-minio",
                "parent": infra_service_id,
                "access-key": key,
                "secret-key": secret
            }
        }
        return self.add(cred)
