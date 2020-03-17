
class Module:

    resource = 'module'

    def __init__(self, nuvla):
        self.nuvla = nuvla

    def find(self, **kvargs):
        return self.nuvla.search(self.resource, **kvargs)

    def get(self, resource_id):
        """
        Returns module identified by `resource_id` as dictionary.
        :param resource_id: str
        :return: dict
        """
        return self.nuvla.get(resource_id).data
