
import re
import time
from typing import Union, Optional, List, Dict
from datetime import datetime, timezone, timedelta

from .base import ResourceBase, ResourceNotFound
from ..api import NuvlaResourceOperationNotAvailable
from ..models import CimiResource, CimiResponse


class DeploymentOperationNotAvailable(Exception):
    pass


class Deployment(ResourceBase):
    """Stateless interface to Nuvla module deployment."""

    STATE_STARTED = 'STARTED'
    STATE_STOPPED = 'STOPPED'
    STATE_ERROR = 'ERROR'

    resource = 'deployment'

    @staticmethod
    def uuid(deployment):
        return Deployment.id(deployment).split('/')[1]

    @staticmethod
    def subtype(deployment):
        return Deployment.module(deployment)['subtype']

    @staticmethod
    def is_component(deployment):
        return Deployment.subtype(deployment) == 'component'

    @staticmethod
    def is_application(deployment):
        return Deployment.subtype(deployment) == 'application'

    @staticmethod
    def is_application_kubernetes(deployment):
        return Deployment.subtype(deployment) == 'application_kubernetes'

    @staticmethod
    def _get_attr(deployment: Union[dict, CimiResource], key):
        if isinstance(deployment, dict):
            return deployment[key]
        else:
            return deployment.data[key]

    @staticmethod
    def module(deployment: Union[dict, CimiResource]):
        key = 'module'
        return Deployment._get_attr(deployment, key)

    @staticmethod
    def module_content(deployment: Union[dict, CimiResource]) -> dict:
        return Deployment.module(deployment)['content']

    @staticmethod
    def acl(deployment: Union[dict, CimiResource]) -> dict:
        key = 'acl'
        return Deployment._get_attr(deployment, key)

    @staticmethod
    def owner(deployment: Union[dict, CimiResource]):
        key = 'owners'
        return Deployment.acl(deployment)[key][0]

    @staticmethod
    def state(deployment: Union[dict, CimiResource]):
        key = 'state'
        return Deployment._get_attr(deployment, key)

    @staticmethod
    def credential_id(deployment: Union[dict, CimiResource]):
        key = 'parent'
        return Deployment._get_attr(deployment, key)

    @staticmethod
    def compatibility(deployment):
        return Deployment.module(deployment).get('compatibility', 'swarm')

    @staticmethod
    def is_compatibility_docker_compose(deployment):
        return Deployment.compatibility(deployment) == 'docker-compose'

    @staticmethod
    def get_port_name_value(port_mapping):
        port_details = port_mapping.split(':')
        return '.'.join([port_details[0], port_details[2]]), port_details[1]

    @staticmethod
    def logs(logs: Union[dict, CimiResource]):
        key = 'log'
        if isinstance(logs, dict):
            return logs.get(key, [])
        else:
            return logs.data.get(key, [])

    @staticmethod
    def urls(deployment: Union[dict, CimiResource]) -> dict:
        if isinstance(deployment, dict):
            d = deployment
        else:
            d = deployment.data
        return dict(d.get('module', {}).get('content', {}).get('urls', []))

    def _set_data(self, deployment: dict, sets=None, records=None,
                  objects=None):
        """
        :param deployment:
        :param sets: [{id: <resource URI>,
                       filter: '', data-type: '',
                       time-start: '', time-end: ''}, ]
                     either `id` or `filter` and `data-type` are required.
        :param records: ['<resource URI>', ]
        :param objects: ['<resource URI>', ]
        :return: None
        Content that goes to deployment. One can provide records and/or objects,
        where ids and/or filter can be provided.
        data:
          records: # optional
            records-ids: [] # optional
            filters: # optional
              - filter: 'filter'
                data-type: 'data-record'
                time-start: 'timestamp'
                time-stop: 'timestamp'
          objects: # optional
            objects-ids: [] # optional
            filters: # optional
              - filter: 'filter'
                data-type: 'data-object'
                time-start: 'timestamp'
                time-stop: 'timestamp'
        """
        data = {}
        if sets:
            for e in sets:
                if 'id' in e:
                    _id = e['id']
                    res = self.nuvla.get(_id)
                    print(dir(res))
                    if not res.data:
                        raise ResourceNotFound('data-set resource not found: {}'.format(_id))
                    if 'data-record-filter' in res.data:
                        data_filter = res.data['data-record-filter']
                        data.setdefault('records', {'filters': []})
                        data['records']['filters'] \
                            .append({'filter': data_filter,
                                     'data-type': 'data-record',
                                     'time-start': e.get('time-start'),
                                     'time-end': e.get('time-end')})
                    if 'data-object-filter' in res.data:
                        data_filter = res.data['data-object-filter']
                        data.setdefault('objects', {'filters': []})
                        data['objects']['filters'] \
                            .append({'filter': data_filter,
                                     'data-type': 'data-object',
                                     'time-start': e.get('time-start'),
                                     'time-end': e.get('time-end')})
                elif ('filter' in e) and ('data-type' in e):
                    data_type = e['data-type']
                    if data_type == 'data-record':
                        data.setdefault('records', {'filters': []})
                        data['records']['filters'] \
                            .append({'filter': e['filter'],
                                     'data-type': data_type,
                                     'time-start': e.get('time-start'),
                                     'time-end': e.get('time-end')})
                    elif data_type == 'data-object':
                        data.setdefault('objects', {'filters': []})
                        data['objects']['filters'] \
                            .append({'filter': e['filter'],
                                     'data-type': data_type,
                                     'time-start': e.get('time-start'),
                                     'time-end': e.get('time-end')})
        if records:
            data.setdefault('records', {})
            data['records'].update({'records-ids': records})
        if objects:
            data.setdefault('objects', {})
            data['objects'].update({'objects-ids': objects})

        if data:
            deployment.update({'data': data})

    def create(self, module_id, infra_cred_id=None, data_sets=None,
               data_records=None, data_objects=None) -> CimiResource:
        """
        Returns deployment as dictionary created from `module_id`.
        Sets `infra_cred_id` infrastructure credentials on the deployment, if given.

        :param module_id: str, resource URI
        :param infra_cred_id: str, resource URI
        :param data_sets: dict, {id: <resource URI>,
                                 filter: <CIMI filter>,
                                 data-type: data-<record | object>,
                                 time-start: <2020-02-24T13:10:30Z>,
                                 time-end: <2020-02-24T13:11:30Z>}
                        either `id` or `filter` and `data-type` are required.
        :param data_records: list of data-record resource URIs
        :param data_objects: list of data-object resource URIs
        :return: CimiResource
        """
        module = {"module": {"href": module_id}}

        deployment_id = self.add(module)

        # Get created deployment and update if needed.
        dpl = self.get(deployment_id)

        updated = False
        if infra_cred_id:
            dpl.data.update({'parent': infra_cred_id})
            updated = True
        if any([data_sets, data_records, data_objects]):
            self._set_data(dpl.data, data_sets, data_records, data_objects)
            updated = True
        if updated:
            try:
                dpl = self.nuvla.edit(deployment_id, dpl.data)
            except Exception as ex:
                raise Exception('Failed editing {0}: {1}'.format(deployment_id, ex))

        return dpl

    def get(self, resource_id) -> CimiResource:
        """
        Returns deployment identified by `resource_id` as dictionary.
        :param resource_id: str
        :return: CimiResource
        """
        return self.nuvla.get(resource_id)

    def get_state(self, resource_id):
        return self.state(self.get(resource_id))

    def _operation(self, resource_id, operation, timeout=0,
                   data: Optional[dict]=None) -> CimiResponse:
        time_max = time.time() + timeout
        while True:
            resource = self.get(resource_id)
            try:
                if operation == 'delete':
                    return self.nuvla.delete(resource_id)
                else:
                    return self.nuvla.operation(resource, operation, data)
            except NuvlaResourceOperationNotAvailable:
                msg = "Operation '{0}' is not available on deployment in state {1}." \
                    .format(operation, Deployment.state(resource))
                print(msg)
                if time.time() >= time_max:
                    raise DeploymentOperationNotAvailable(msg)
                else:
                    time.sleep(3)

    def start(self, resource_id, timeout=0):
        return self._operation(resource_id, 'start', timeout)

    def stop(self, resource_id, timeout=0):
        return self._operation(resource_id, 'stop', timeout)

    def delete(self, resource_id, timeout=0):
        return self._operation(resource_id, 'delete', timeout)

    def launch(self, module_id, infra_cred_id=None, data_sets=None,
               data_records=None, data_objects=None) -> CimiResource:
        dpl = self.create(module_id, infra_cred_id=infra_cred_id, data_sets=data_sets,
                          data_records=data_records, data_objects=data_objects)
        self.start(dpl.id)
        return self.get(dpl.id)

    def terminate(self, resource_id: str, timeout=30) -> CimiResponse:
        """Stops and deletes the deployment. Waits at max `timeout` seconds for
        the deployment to be fully stoped before attemting deletion.
        """
        self.stop(resource_id)
        return self.delete(resource_id, timeout=timeout)

    def list(self) -> List[Dict]:
        res = self.nuvla.search(self.resource)
        if res.count < 1:
            return []
        return res.data['resources']

    def init_logs(self, deployment: CimiResource, service: str,
                  since: Optional[datetime] = None) -> CimiResource:
        """
        Creates and returns `deployment-log` resource that corresponds to the
        logs of `service` from `deployment` and starting from `since`.
        :param deployment: CimiResource
        :param service: str
        :param since: datetime
        :return: CimiResource
        """
        if not since:
            fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            t = datetime.strptime(deployment.data['created'], fmt)
            # Give a bit of slack.
            td = timedelta(minutes=5)
            since = t - td
        since_str = since.replace(tzinfo=timezone.utc) \
            .replace(second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        request = {'service': 'Service/{}'.format(service),
                   'since': since_str}
        resp = self._operation(deployment.id, 'create-log', data=request)
        logs_id = resp.data['resource-id']
        return self.nuvla.get(logs_id)

    def get_logs(self, logs: CimiResource) -> CimiResource:
        """
        Get `service` logs from `since` till now.
        :param logs: CimiResource
        :return: list: list of lines of the log
        """
        # Request fetching of logs from container.
        self.nuvla.operation(logs, 'fetch')
        # Wait for logs to be produced.
        time.sleep(5)
        # Get the resource. It may contain the logs.
        return self.nuvla.get(logs.id)

    def _template_interpolation(self, string: str, params: dict) -> str:
        """Returns `string` interpolated by the values from `params`.
        Returns an empty string, if either of those is emtpy: `string`, `params`
        or the value of the required interpolation key.
        Throws ValueError if `params` is missing substitution keys defined in
        `string`.
        """
        if not string:
            return ''
        groups = re.findall(r'(\${.*?})', string)
        if len(groups) > 0 and not params:
            raise ValueError('no substitutions provided.')
        groups_keys = list(map(lambda x: x.replace('${','').replace('}',''),
                            groups))
        for k in groups_keys:
            # If the interpolant from the string (key in groups_keys) is not in
            # the list of parameters (params.keys()), interpolation is not possible.
            if k not in params:
                raise ValueError(f'{k} is missing in params')
            if not params[k]:
                return ''
            string = re.compile('\${' + k + '}').sub(params[k], string)
        return string

    def get_url(self, deployment: CimiResource, name) -> Union[str, None]:
        """Returns interpolated URL defined by `name` in deployment.
        Returns an empty string if not all deployment parameters required
        for interpolation are filled with values.
        Returns None if either URL `name` is not present on the deployment or
        interpolation is not possible due to missing deployment parameters. This
        means obtaining URL will not be possible.
        """
        url = self.urls(deployment).get(name)
        if not url:
            return None
        params = self.get_parameters(self.id(deployment.data))
        # Flatten parameters map.
        flat_params = {}
        for v in params.values():
            flat_params.update(v)
        try:
            return self._template_interpolation(url, flat_params)
        except ValueError as ex:
            print(ex)
            return None

    def create_parameter(self, resource_id, user_id, param_name, param_value=None,
                         node_id=None, param_description=None):
        parameter = {'name': param_name,
                     'parent': resource_id,
                     'acl': {'owners': ['group/nuvla-admin'],
                             'edit-acl': [user_id]}}
        if node_id:
            parameter['node-id'] = node_id
        if param_description:
            parameter['description'] = param_description
        if param_value:
            parameter['value'] = param_value
        return self.nuvla.add('deployment-parameter', parameter)

    def _get_parameter(self, resource_id, param_name, node_id=None, select=None):
        filters = f"parent='{resource_id}' and name='{param_name}'"
        if node_id:
            filters += " and node-id='{}'".format(node_id)
        res = self.nuvla.search("deployment-parameter", filter=filters, select=select)
        if res.count < 1:
            raise ResourceNotFound(f'Deployment parameter "{filters}" not found.')
        return res.resources[0]

    def get_parameter(self, resource_id, node_id, param_name):
        """Returns value of deployment `resource_id` parameter `name`. To get
        global level parameters (not belonging to a node), provide '' or None
        as `node_id`.
        Returns None if parameter is not found.
        """
        try:
            param = self._get_parameter(resource_id, param_name, node_id)
        except ResourceNotFound:
            return None
        return param.data.get('value')

    def get_parameters(self, resource_id, node_id='') -> Union[list, dict]:
        """When `node_id` is not provided, returns dictionary with all
        parameters
        {'global': {'<param name>': '<param value>', },
         '<node_id>': {'<param name>': '<param value>', },
         ...}
        'global' key corresponds to node_id == None or ''.
        Returns list with parameters for the provided `node_id`.
        Returns empty list or dict if parameters were not found.
        """
        fltr = f"parent='{resource_id}'"
        if node_id:
            fltr += f" and node-id='{node_id}'"
            params = []
        else:
            params = {}
        res = self.nuvla.search('deployment-parameter', filter=fltr)
        for p in res.resources:
            d = {p.data['name']: p.data.get('value')}
            if node_id:
                params.append(d)
            else:
                if 'node-id' in p.data:
                    params.setdefault(p.data['node-id'], {}).update(d)
                else:
                    params.setdefault('global', {}).update(d)
        return params

    def update_port_parameters(self, deployment: dict, ports_mapping):
        if ports_mapping:
            for port_mapping in ports_mapping.split():
                port_param_name, port_param_value = self.get_port_name_value(port_mapping)
                self.set_parameter(Deployment.id(deployment), Deployment.uuid(deployment),
                                   port_param_name, port_param_value)

    def set_parameter(self, resource_id, node_id, name, value):
        if not isinstance(value, str):
            raise ValueError('Parameter value should be string.')
        param = self._get_parameter(resource_id, name, node_id=node_id, select='id')
        return self.nuvla.edit(param.id, {'value': value})

    def set_parameter_ignoring_errors(self, resource_id, node_id, name, value):
        try:
            self.set_parameter(resource_id, node_id, name, value)
        except Exception as _:
            pass

    def set_parameter_create_if_needed(self, resource_id, user_id, param_name,
                                       node_id=None, param_value=None,
                                       param_description=None):
        try:
            self.set_parameter(resource_id, node_id, param_name, param_value)
        except ResourceNotFound as _:
            self.create_parameter(resource_id, user_id, param_name,
                                  param_value=param_value, node_id=node_id,
                                  param_description=param_description)

    def set_infra_cred_id(self, resource_id, infra_cred_id):
        try:
            return self.nuvla.edit(resource_id, {'parent': infra_cred_id}).data
        except Exception as ex:
            raise Exception('ERROR: Failed to edit {0}: {1}'.format(resource_id, ex))

    def set_state(self, resource_id, state):
        self.nuvla.edit(resource_id, {'state': state})

    def set_state_started(self, resource_id):
        self.set_state(resource_id, self.STATE_STARTED)

    def set_state_stopped(self, resource_id):
        self.set_state(resource_id, self.STATE_STOPPED)

    def set_state_error(self, resource_id):
        self.set_state(resource_id, self.STATE_ERROR)
