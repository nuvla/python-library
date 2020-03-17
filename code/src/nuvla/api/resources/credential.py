
class Credential(object):

    def __init__(self, nuvla):
        self.nuvla = nuvla

    def find(self, infra_service_id):
        """
        Returns list of credentials for `infra_service_id` infrastructure service.
        :param infra_service_id: str, URI
        :return: list
        """
        filters = "parent='{}'".format(infra_service_id)
        creds = self.nuvla.search('credential', filter=filters, select="id")
        return creds.resources


