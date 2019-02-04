# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import warnings
import collections

from threading import Lock


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def truncate_middle(max_len, message, truncate_message='...'):
    if message and max_len and len(message) > max_len:
        subsize = int((max_len - len(truncate_message)) / 2)
        message = message[0:subsize] + truncate_message + message[-subsize:]
    return message


class CimiResponse(object):

    def __init__(self, json):
        self.json = json
        self._attributes_names = []
        self.extract_and_set_attributes()

    def extract_and_set_attributes(self):
        for key, value in list(self.json.items()):
            name = camel_to_snake(key)
            if hasattr(self, name):
                warnings.warn('Cannot set attribute "{0}" because it already exist'.format(name), RuntimeWarning)
            else:
                setattr(self, name, value)
                self._attributes_names.append(name)

    def __str__(self):
        data = ['{0}: {1}'.format(attr, truncate_middle(80, str(getattr(self, attr))))
                for attr in self._attributes_names
                if getattr(self, attr, None) is not None]
        return '{0}:\n{1}'.format(self.__class__.__name__, '\n'.join(sorted(data)))


class CimiResource(CimiResponse):

    def __init__(self, json):
        super(CimiResource, self).__init__(json)
        self.operations_by_name = self.get_operations_by_name()

    def get_operations_by_name(self):
        operations = self.json.get('operations', [])
        return dict([(op['rel'], op) for op in operations if 'rel' in op])


class CimiCollection(CimiResource):

    def __init__(self, json, resource_type):
        super(CimiCollection, self).__init__(json)
        self.resource_type = resource_type
        self.__lock_iter = Lock()
        self.__lock_list = Lock()
        self.__resources = []
        self.__json_resources = self.json.get(self.resource_type, [])

    def resources(self):
        for i in range(len(self.__json_resources)):
            with self.__lock_iter:
                if i < len(self.__resources):
                    yield self.__resources[i]
                else:
                    resource = CimiResource(self.__json_resources[i])
                    self.__resources.append(resource)
                    yield resource

    @property
    def resources_list(self):
        with self.__lock_list:
            if len(self.__resources) != len(self.__json_resources):
                list(self.resources())
            return self.__resources

    def __iter__(self):
        return self.resources()


class CloudEntryPoint(CimiResource):

    def __init__(self, json):
        super(CloudEntryPoint, self).__init__(json)
        self.entry_points = self.extract_entry_points()

    def extract_entry_points(self):
        return dict([(k, v['href']) for k, v in list(self.json.items()) if isinstance(v, dict) and 'href' in v])


App = collections.namedtuple('App', [
    'name',
    'type',
    'version',
    'path',
])

Deployment = collections.namedtuple('Deployment', [
    'id',
    'module',
    'status',
    'started_at',
    'last_state_change',
    'clouds',
    'username',
    'abort',
    'service_url',
    'scalable',
])

Node = collections.namedtuple('Node', [
    'path',
    'name',
    'cloud',
    'multiplicity',
    'max_provisioning_failures',
    'network',
    'cpu',
    'ram',
    'disk',
    'extra_disk_volatile',
])

VirtualMachine = collections.namedtuple('VirtualMachine', [
    'id',
    'cloud',
    'status',
    'deployment_id',
    'deployment_owner',
    'node_name',
    'node_instance_id',
    'ip',
    'cpu',
    'ram',
    'disk',
    'instance_type',
    'is_usable',
])

Usage = collections.namedtuple('Usage', [
    'cloud',
    'run_usage',
    'vm_usage',
    'inactive_vm_usage',
    'others_vm_usage',
    'pending_vm_usage',
    'unknown_vm_usage',
    'quota',
])

ModuleParameter = collections.namedtuple('ModuleParameter', [
    'name',
    'value',
    'defaultValue',
    'category',
    'description',
    'isSet',
    'mandatory',
    'readonly',
    'type',
    'instructions',
])

Module = collections.namedtuple('Module', [
    'name',
    'type',
    'created',
    'modified',
    'description',
    'version',
    'path',
])

CloudImageIdentifier = collections.namedtuple('CloudImageIdentifier', [
    'cloud',
    'identifier',
])

UserItem = collections.namedtuple('UserItem', [
    'username',
    'email',
    'first_name',
    'last_name',
    'organization',
    'roles',
    'privileged',
    'active_since',
    'last_online',
    'online',
])

User = collections.namedtuple('User', UserItem._fields + (
    'cyclone_login',
    'github_login',
    'configured_clouds',
    'default_cloud',
    'ssh_public_keys',
    'keep_running',
    'timeout',
))
