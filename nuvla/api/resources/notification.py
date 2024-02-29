
from .base import ResourceBase


class Notification(ResourceBase):

    resource = 'notification'

    def create(self, message, category, content_unique_id,
               target_resource=None, not_before=None, expiry=None,
               callback_id=None, callback_msg=None, acl=None):

        notification = {'message': message,
                        'category': category,
                        'content-unique-id': content_unique_id}

        if target_resource:
            notification.update({'target-resource': target_resource})
        if not_before:
            notification.update({'not-before': not_before})
        if expiry:
            notification.update({'expiry': expiry})
        if callback_id:
            notification.update({'callback': callback_id})
        if callback_msg:
            notification.update({'callback-msg': callback_msg})
        if acl:
            notification.update({'acl': acl})

        return self.add(notification)

    def find_by_content_unique_id(self, content_unique_id):
        resp = self.nuvla.search(self.resource,
                                 filter="content-unique-id='{}'".format(content_unique_id))
        if resp.count < 1:
            return None
        else:
            return list(resp.resources)[0]

    def exists_with_content_unique_id(self, content_unique_id):
        return self.find_by_content_unique_id(content_unique_id) is not None
