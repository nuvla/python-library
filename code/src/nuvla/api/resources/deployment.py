
from .utils import check_created, ResourceNotFound
from ..api import Api as Nuvla


class Deployment(object):
    """Stateless interface to Nuvla module deployment."""

    STATE_STARTED = 'STARTED'
    STATE_STOPPED = 'STOPPED'
    STATE_ERROR = 'ERROR'

    resource = 'deployment'

    @staticmethod
    def id(deployment):
        return deployment['id']

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
    def module(deployment):
        return deployment['module']

    @staticmethod
    def module_content(deployment):
        return Deployment.module(deployment)['content']

    @staticmethod
    def owner(deployment):
        return deployment['acl']['owners'][0]

    @staticmethod
    def state(deployment):
        return deployment['state']

    @staticmethod
    def credential_id(deployment):
        return deployment['parent']

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

    def __init__(self, nuvla: Nuvla):
        self.nuvla = nuvla

    def _set_data(self, deployment, sets=None, records=None, objects=None):
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
               data_records=None, data_objects=None):
        """
        Returns deployment as dictionary created from `module_id`.
        Sets `infra_cred_id` infrastructure credentials on the deployment, if given.

        :param module_id: str, resource URI
        :param infra_cred_id: str, resource URI
        :param data_sets: dict, {id: <resource URI>,
                                 filter: <CIMI filter>,
                                 data-type: <record | object>,
                                 time-start: <2020-02-24T13:10:30Z>,
                                 time-end: <2020-02-24T13:11:30Z>}
                        either `id` or `filter` and `data-type` are required.
        :param data_records: list of data-record resource URIs
        :param data_objects: list of data-object resource URIs
        :return: dict
        """
        module = {"module": {"href": module_id}}

        res = self.nuvla.add(self.resource, module)
        deployment_id = check_created(res, 'Failed to create deployment.')

        deployment = self.get(deployment_id)

        if infra_cred_id:
            deployment.update({'parent': infra_cred_id})
        self._set_data(deployment, data_sets, data_records, data_objects)
        try:
            return self.nuvla.edit(deployment_id, deployment).data
        except Exception as ex:
            raise Exception('ERROR: Failed to edit {0}: {1}'.format(deployment_id, ex))

    def get(self, resource_id):
        """
        Returns deployment identified by `resource_id` as dictionary.
        :param resource_id: str
        :return: dict
        """
        return self.nuvla.get(resource_id).data

    def start(self, resource_id):
        return self.nuvla.operation(resource_id, 'start')

    def stop(self, resource_id):
        return self.nuvla.operation(resource_id, 'stop')

    def delete(self, resource_id):
        return self.nuvla.delete(resource_id)

    def launch(self, module_id, infra_cred_id=None, data_sets=None,
               data_records=None, data_objects=None):
        dpl = self.create(module_id, infra_cred_id=infra_cred_id, data_sets=data_sets,
                          data_records=data_records, data_objects=data_objects)
        rid = self.id(dpl)
        self.start(rid)
        return rid

    def terminate(self, resource_id):
        self.stop(resource_id)
        self.delete(resource_id)

    def _create_log(self, resource_id):
        pass

    def get_logs(self, resource_id):
        pass

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

    def _get_parameter(self, resource_id, node_id, name, select=None):
        filters = "parent='{0}' and node-id='{1}' and name='{2}'".format(resource_id, node_id, name)
        res = self.nuvla.search("deployment-parameter", filter=filters, select=select)
        if res.count < 1:
            raise ResourceNotFound('Deployment parameter "{0}" not found.'.format(filters))
        return res.resources[0]

    def get_parameter(self, resource_id, node_id, name):
        try:
            param = self._get_parameter(resource_id, node_id, name)
        except ResourceNotFound:
            return None
        return param.data.get('value')

    def update_port_parameters(self, deployment, ports_mapping):
        if ports_mapping:
            for port_mapping in ports_mapping.split():
                port_param_name, port_param_value = self.get_port_name_value(port_mapping)
                self.set_parameter(Deployment.id(deployment), Deployment.uuid(deployment),
                                   port_param_name, port_param_value)

    def set_parameter(self, resource_id, node_id, name, value):
        if not isinstance(value, str):
            raise ValueError('Parameter value should be string.')
        param = self._get_parameter(resource_id, node_id, name, select='id')
        return self.nuvla.edit(param.id, {'value': value})

    def set_parameter_ignoring_errors(self, resource_id, node_id, name, value):
        try:
            self.set_parameter(resource_id, node_id, name, value)
        except Exception as _:
            pass

    def set_parameter_create_if_needed(self, resource_id, user_id, param_name, param_value=None,
                                       node_id=None, param_description=None):
        try:
            self.set_parameter(resource_id, node_id, param_name, param_value)
        except ResourceNotFound as _:
            self.create_parameter(resource_id, user_id, param_name, param_value,
                                  node_id, param_description)

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
