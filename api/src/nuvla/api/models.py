# -*- coding: utf-8 -*-

from threading import Lock


def truncate_middle(max_len, message, truncate_message='...'):
    if message and max_len and len(message) > max_len:
        subsize = int((max_len - len(truncate_message)) / 2)
        message = message[0:subsize] + truncate_message + message[-subsize:]
    return message


class CimiResponse(object):

    def __init__(self, data):
        self.data = data

    def __str__(self):
        attr_list = ['{0}: {1}'.format(k, truncate_middle(80, str(v))) for k, v in list(self.data.items())]
        return '{0}:\n{1}'.format(self.__class__.__name__, '\n'.join(sorted(attr_list)))


class CimiResource(CimiResponse):

    def __init__(self, data):
        super(CimiResource, self).__init__(data)
        self.id = data.get('id')
        self.resource_type = data.get('resource-type')
        self.__operations = None

    @property
    def operations(self):
        if self.__operations is None:
            self.__operations = dict([(op['rel'], op) for op in self.data.get('operations', []) if 'rel' in op])
        return self.__operations


class CimiCollection(CimiResource):

    def __init__(self, data):
        super(CimiCollection, self).__init__(data)
        self.count = self.data.get('count')
        self.__lock_iter = Lock()
        self.__lock_list = Lock()
        self.__resources = []
        self.__json_resources = self.data.get('resources', [])

    def resources_generator(self):
        for i in range(len(self.__json_resources)):
            with self.__lock_iter:
                if i < len(self.__resources):
                    yield self.__resources[i]
                else:
                    resource = CimiResource(self.__json_resources[i])
                    self.__resources.append(resource)
                    yield resource

    @property
    def resources(self):
        with self.__lock_list:
            if len(self.__resources) != len(self.__json_resources):
                list(self.resources_generator())
            return self.__resources

    def __iter__(self):
        return self.resources_generator()


class CloudEntryPoint(CimiResource):

    def __init__(self, data):
        super(CloudEntryPoint, self).__init__(data)
        self.collections = self._extract_entry_points()
        self.base_uri = self.data['base-uri']

    def _extract_entry_points(self):
        return dict([(k, v['href']) for k, v in list(self.data.get('collections').items())])
