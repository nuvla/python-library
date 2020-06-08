
from typing import Union

from nuvla.api import Api as Nuvla
from nuvla.api.models import CimiResource


class ResourceNotFound(Exception):
    pass


class ResourceCreateError(Exception):
    def __init__(self, reason, response=None):
        super(ResourceCreateError, self).__init__(reason)
        self.reason = reason
        self.response = response


def check_created(resp, errmsg=''):
    """
    Returns id of the created resource or raises ResourceCreateError.
    :param resp: nuvla.api.models.CimiResponse
    :param errmsg: error message
    :return: str, resource id
    """
    if resp.data['status'] == 201:
        return resp.data['resource-id']
    else:
        if errmsg:
            msg = '{0} : {1}'.format(errmsg, resp.data['message'])
        else:
            msg = resp.data['message']
        raise ResourceCreateError(msg, resp)


class ResourceBase:

    resource = None

    @staticmethod
    def id(resource: Union[dict, CimiResource]):
        key = 'id'
        if isinstance(resource, dict):
            return resource[key]
        else:
            return resource.data[key]

    def __init__(self, nuvla: Nuvla):
        self.nuvla = nuvla
        if not self.resource:
            raise Exception('resource type not set.')

    def add(self, data: dict) -> str:
        """Creates resource of type `self.resource` using provided `data`.
        Returns created resource ID.
        """
        return check_created(self.nuvla.add(self.resource, data),
                             f'Failed to create {self.resource}.')

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
