
class Credential(object):

    @staticmethod
    def id(credential):
        return credential['id']

    def __init__(self, nuvla):
        self.nuvla = nuvla

    def find_parent(self, parent):
        filters = "parent='{}'".format(parent)
        creds = self.nuvla.search('credential', filter=filters, select="id")
        return creds.resources

    def find(self, infra_service_id):
        """
        Returns list of credentials for `infra_service_id` infrastructure service.
        :param infra_service_id: str, URI
        :return: list
        """
        return self.find_parent(infra_service_id)

    def delete(self, resource_id):
        return self.nuvla.delete(resource_id)


