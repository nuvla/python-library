
import os
import re
from ..api import NuvlaError
from .base import ResourceBase


APP_TYPE_K8S = 'application_kubernetes'
APP_TYPE_DOCKER = 'application'


class Module(ResourceBase):

    resource = 'module'

    TYPE_PROJECT = 'project'
    TYPE_COMPONENT = 'component'
    TYPE_APPLICATION = 'application'

    def find(self, **kvargs):
        return self.nuvla.search(self.resource, **kvargs)

    def get_by_path(self, path, version=-1) -> dict:
        res = self.nuvla.search(self.resource, filter="path='{}'".format(path))
        if res.count == 0:
            return {}
        return self.get_by_id(res.resources[0].id)

    def create(self, module: dict, exist_ok=False) -> str:
        """
        Adds new `module` of type project, component and application.
        Modules of different types can be built by ProjectBuilder, AppBuilderK8s,
        AppBuilderDocker, ComponentBuilder.

        :param module: dict
        :return: str:
        """
        no_author_in_apps = module['subtype'] != self.TYPE_PROJECT and \
                            'author' not in module['content']
        if no_author_in_apps:
            module['content']['author'] = self.nuvla._username
        try:
            response = self.nuvla.add(self.resource, module)
            return response.data['resource-id']
        except NuvlaError as ex:
            if re.match('path.*already exist', ex.reason) and exist_ok:
                res = self.nuvla.search(self.resource,
                                        filter="path='{}'".format(module['path']))
                return res.resources[0].id
            else:
                raise ex

    def get_by_id(self, resource_id) -> dict:
        """
        Returns module identified by `resource_id` as dictionary.
        :param resource_id: str
        :return: dict
        """
        return self.nuvla.get(resource_id).data

    def update(self, module: dict) -> dict:
        res = self.nuvla.edit(module['id'], module)
        return res.data

    def get_urls(self, module_id) -> dict:
        res = self.nuvla.get(module_id)
        return dict(res.data.get('content', {}).get('urls'))


class ModuleBuilder:

    module_requires = ['path']
    type = None

    _type_not_set_err = 'module type is not set (subtype)'

    def __init__(self, base=None):
        if base:
            self.module = base
        else:
            self.module = {}

    def name(self, name):
        if name:
            self.module['name'] = name
        return self

    def description(self, desc):
        if desc:
            self.module['description'] = desc
        return self

    def path(self, path):
        """
        Required to build.
        :param path: full path to the module
        :return: ModuleBuilder
        """
        path = path.lstrip('/')
        self.module['parent-path'] = os.path.dirname(path)
        self.module['path'] = path
        return self

    def build(self):
        if not self.type:
            raise Exception(self._type_not_set_err)
        self.module['subtype'] = self.type
        for r in self.module_requires:
            if r not in self.module:
                raise Exception('{} is missing in module.'.format(r))
        if 'name' not in self.module:
            self.module['name'] = os.path.basename(self.module['path'])
        if 'description' not in self.module:
            self.module['description'] = self.module['name']
        return self.module


class ProjectBuilder(ModuleBuilder):
    type = 'project'

    def __init__(self, base=None):
        super().__init__(base)


class ComponentBuidler(ModuleBuilder):
    type = 'component'

    def __init__(self, base=None):
        super().__init__(base)


class AppBuilder(ModuleBuilder):

    type = 'application'

    module_requires_app = ['content']

    script_key = None
    content_requires = []

    def __init__(self, base=None):
        super().__init__(base)
        self.module_requires.extend(self.module_requires_app)
        if not self.script_key:
            raise Exception('')
        self.content_requires.append(self.script_key)

    def logo_url(self, url):
        self.module['logo-url'] = url
        return self

    def author(self, name):
        self.module.setdefault('content', {})['author'] = name
        return self

    def commit(self, message):
        self.module.setdefault('content', {})['commit'] = message
        return self

    def env_var(self, name, value='', required=False, description=''):
        """
        Can be called multiple times to set a list of environment variables.
        :param name:
        :param value:
        :param required:
        :param description:
        :return:
        """
        env_var = {'name': name, 'value': value,
                   'required': required, 'description': description}
        self.module.setdefault('content', {}) \
            .setdefault('environmental-variables', []).append(env_var)
        return self

    def url(self, name, value):
        """
        Can be called multiple times to set a list of URLs.
        :param name:
        :param value:
        :return:
        """
        self.module.setdefault('content', {}) \
            .setdefault('urls', []).append([name, value])
        return self

    def output_parm(self, name, description=''):
        """
        Can be called multiple times to set a list of output parameters.
        :param name:
        :param description:
        :return:
        """
        param = {"name": name, "description": description or name}
        self.module.setdefault('content', {}) \
            .setdefault('output-parameters', []).append(param)
        return self

    def files(self, name, content):
        """
        Can be called multiple times to set a list of files.
        :param name:
        :param content:
        :return:
        """
        self.module.setdefault('content', {}) \
            .setdefault('files', []).append([name, content])
        return self

    def script(self, content):
        """
        Required to build. Content of the deployment script.
        :param content: string.
        :return:
        """
        if not self.script_key:
            raise Exception('script type should be set')
        self.module.setdefault('content', {})[self.script_key] = content
        return self

    def data_content_type(self, type):
        self.module.setdefault('data-accept-content-types', []) \
            .append(type)
        return self

    def registry(self, resource_id):
        self.module.setdefault('content', []) \
            .setdefault('private-registries', []) \
            .append(resource_id)
        return self

    def build(self) -> dict:
        """
        Builds and returns module as a dictionary.
        :return: dict
        """
        if 'commit' not in self.module['content']:
            self.module['content']['commit'] = 'no commit message'
        for r in self.content_requires:
            if r not in self.module['content']:
                raise Exception('{} is missing in module["content"].'.format(r))
        return super(AppBuilder, self).build()


class AppBuilderK8s(AppBuilder):
    type = APP_TYPE_K8S
    script_key = 'docker-compose'


class AppBuilderDocker(AppBuilder):
    type = APP_TYPE_DOCKER
    script_key = 'docker-compose'

