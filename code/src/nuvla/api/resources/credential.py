
from nuvla.api import Api as Nuvla


class Credential:

    resource = 'credential'

    def __init__(self, nuvla: Nuvla):
        self.nuvla = nuvla

    def find(self, infra_service_id):
        """
        Returns list of credentials for `infra_service_id` infrastructure service.
        :param infra_service_id: str, URI
        :return: list
        """
        filters = "parent='{}'".format(infra_service_id)
        creds = self.nuvla.search(self.resource, filter=filters, select="id")
        return creds.resources


class CredentialK8s(Credential):

    def add(self, ca, cert, key, infra_service_id, name, description=None):
        iscred_k8s = {
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
        res = self.nuvla.add(self.resource, iscred_k8s)
        return res.data['resource-id']