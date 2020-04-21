
from nuvla.api import Api as Nuvla

class ResourceBase:

    resource = None

    def __init__(self, nuvla: Nuvla):
        self.nuvla = nuvla
        if not self.resource:
            raise Exception('resource type not set.')

    def add(self, data: dict) -> str:
        """Creates resource of type `self.resource` using provided `data`.
        Returns created resource ID.
        """
        response = self.nuvla.add(self.resource, data)
        return response.data['resource-id']

    def get(self, resource_id: str) -> dict:
        """Returns document identified by `resource_id`.
        """
        return self.nuvla.get(resource_id).data

    def delete(self, resource_id: str) -> str:
        """Deletes resource identified by `resource_id`. Returns resource ID.
        """
        response = self.nuvla.delete(resource_id)
        return response.data['resource-id']

    def id_by_name(self, name, filter=None) -> list:
        """Returns list of resource IDs with name equals to `name`. In most
        cases the length of the list will be 0 or 1.
        """
        fltr = f"name='{name}'"
        if filter:
           fltr += f' and {filter}'
        res = self.nuvla.search(self.resource, filter=fltr)
        return [r.data['id'] for r in res.resources]

