
from .base import ResourceBase


class Callback(ResourceBase):

    resource = 'callback'

    def create(self, action_name, target_resource, data=None, expires=None, acl=None):
        """
        :param action_name: name of the action
        :param target_resource: resource id
        :param data: dict
        :param expires: ISO timestamp
        :param acl: acl
        :return:
        """

        callback = {"action": action_name,
                    "target-resource": {'href': target_resource}}

        if data:
            callback.update({"data": data})
        if expires:
            callback.update({"expires": expires})
        if acl:
            callback.update({"acl": acl})

        return self.add(callback)
