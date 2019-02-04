# -*- coding: utf-8 -*-
#
# (C) Copyright 2017 SixSq (http://sixsq.com/).
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
 Python wrapper of the SlipStream API (http://ssapi.sixsq.com).


 Install
 -------

 Latest release from pypi
 ~~~~~~~~~~~~~~~~~~~~~~~~
 .. code-block:: Bash
 
   $ pip install slipstream-api
 
 Most recent version from source code
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 .. code-block:: Bash
 
   $ pip install 'https://github.com/slipstream/SlipStreamPythonAPI/archive/master.zip'

 
 Usage
 -----
 To use this library, import it and instanciate it.
 Then use one of the method to login.::
    from slipstream.api import Api
 
    api = Api()

    api.login_internal('username', 'password')

 
 Examples
 --------

 Login on Nuvla with username and password
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    api.login_internal('username', 'password')


 Login on Nuvla with key and secret
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    api.login_apikey('credential/ce02ef40-1342-4e68-838d-e1b2a75adb1e', 
                     'the-secret-key')


 List applications from the App Store
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    from pprint import pprint as pp
    pp(list(api.list_applications()))


 List base images
 ~~~~~~~~~~~~~~~~
 ::

    from pprint import pprint as pp
    pp(list(api.list_project_content('examples/images')))


 Simple component deployment (WordPress server)
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::
 
    # Deploy the WordPress component
    deployment_id = api.deploy('apps/WordPress/wordpress')
 
 
 Complete application deployment (WordPress server)
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    # Cloud
    cloud = 'exoscale-ch-gva'

    # WordPress Title
    wordpress_title = 'WordPress deployed by SlipStream through SlipStreamPythonAPI'
    
    # Create the dict of parameters to (re)define
    parameters = dict(wordpress_title=wordpress_title)
    
    # Deploy the WordPress component
    deployment_id = api.deploy('apps/WordPress/wordpress', cloud, parameters)
    
    # Wait the deployment to be ready
    while api.get_deployment(deployment_id).status != 'ready': time.sleep(10)
    
    # Print the WordPress URL
    print api.get_deployment(deployment_id).service_url

    # Print the WordPress admin username and password
    print api.get_deployment_parameter(deployment_id, 'machine:admin_email')
    print api.get_deployment_parameter(deployment_id, 'machine:admin_password')


 Terminate a deployment
 ~~~~~~~~~~~~~~~~~~~~~~
 ::

    api.terminate(deployment_id)

    
 API documentation
 -----------------

"""

from __future__ import absolute_import

import os
import six
import stat
import uuid
import logging

import requests
from requests.cookies import MockRequest
from requests.exceptions import HTTPError, ConnectionError

from six import string_types, integer_types
from six.moves.urllib.parse import urlparse
from six.moves.http_cookiejar import MozillaCookieJar

from . import models

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = 'https://nuv.la'
DEFAULT_COOKIE_FILE = os.path.expanduser('~/.slipstream/cookies.txt')
HREF_SESSION_TMPL_INTERNAL = 'session-template/internal'
HREF_SESSION_TMPL_APIKEY = 'session-template/api-key'


def _mod_url(path):
    parts = path.strip('/').split('/')
    if parts[0] == 'module':
        del parts[0]
    return '/module/' + '/'.join(parts)


def _mod(path, with_version=True):
    parts = path.split('/')
    if with_version:
        return '/'.join(parts[1:])
    else:
        return '/'.join(parts[1:-1])


def get_module_type(category):
    mapping = {'image': 'component',
               'deployment': 'application'}
    return mapping.get(category.lower(), category.lower())


def element_tree__iter(root):
    return getattr(root, 'iter',  # Python 2.7 and above
                   root.getiterator)  # Python 2.6 compatibility


class SlipStreamError(Exception):
    def __init__(self, reason, response=None):
        super(SlipStreamError, self).__init__(reason)
        self.reason = reason
        self.response = response


class SessionStore(requests.Session):
    """A ``requests.Session`` subclass implementing a file-based session store."""

    def __init__(self, endpoint, reauthenticate, cookie_file=None, login_params=None):
        super(SessionStore, self).__init__()
        self.session_base_url = '{0}/api/session'.format(endpoint)
        self.reauthenticate = reauthenticate
        self.login_params = login_params
        if cookie_file is None:
            cookie_file = DEFAULT_COOKIE_FILE
        cookie_dir = os.path.dirname(cookie_file)
        self.cookies = MozillaCookieJar(cookie_file)
        # Create the $HOME/.slipstream dir if it doesn't exist
        if not os.path.isdir(cookie_dir):
            os.mkdir(cookie_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        # Load existing cookies if the cookies.txt exists
        if os.path.isfile(cookie_file):
            self.cookies.load(ignore_discard=True)
            self.cookies.clear_expired_cookies()

    def need_to_login(self, accessed_url, status_code):
        return self.reauthenticate and status_code in [401, 403] and accessed_url != self.session_base_url

    def _request(self, *args, **kwargs):
        return super(SessionStore, self).request(*args, **kwargs)

    def request(self, *args, **kwargs):
        response = self._request(*args, **kwargs)

        if not self.verify and response.cookies:
            self._unsecure_cookie(args[1], response)
        if 'Set-Cookie' in response.headers:
            self.cookies.save(ignore_discard=True)

        url = args[1]
        if self.need_to_login(url, response.status_code):
            login_response = self.cimi_login(self.login_params)
            if login_response is not None and login_response.status_code == 201:
                # retry the call after reauthentication
                response = self._request(*args, **kwargs)

        return response

    def cimi_login(self, login_params):
        self.login_params = login_params
        if self.login_params:
            return self.request('POST', self.session_base_url,
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json'},
                                json={'sessionTemplate': login_params})
        else:
            return None

    def _unsecure_cookie(self, url_str, response):
        url = urlparse(url_str)
        if url.scheme == 'http':
            for cookie in response.cookies:
                cookie.secure = False
                self.cookies.set_cookie_if_ok(cookie, MockRequest(response.request))

    def clear(self, domain):
        """Clear cookies for the specified domain."""
        try:
            self.cookies.clear(domain)
            self.cookies.save()
        except KeyError:
            pass


def to_login_params(creds):
    """
    :param creds: {'username': '', 'password': ''} or {'key': '', 'secret': ''}
    :return: dict extended with the right 'href' or an empty dict
    """
    if not creds:
        return {}
    if ('username' in creds) and ('password' in creds):
        creds.update({'href': HREF_SESSION_TMPL_INTERNAL})
    elif ('key' in creds) and ('secret' in creds):
        creds.update({'href': HREF_SESSION_TMPL_APIKEY})
    else:
        return {}
    return creds


class Api(object):
    """ This class is a Python wrapper&helper of the native SlipStream REST API"""

    GLOBAL_PARAMETERS = ['bypass-ssh-check', 'refqname', 'keep-running', 'tags', 'mutable', 'type']
    KEEP_RUNNING_VALUES = ['always', 'never', 'on-success', 'on-error']
    CIMI_PARAMETERS_NAME = ['first', 'last', 'filter', 'select', 'expand', 'orderby', 'aggregation']

    def __init__(self, endpoint=DEFAULT_ENDPOINT, cookie_file=None, insecure=False, reauthenticate=False,
                 login_creds=None):
        """
        :param endpoint: SlipStream endpoint (https://nuv.la).
        :param cookie_file: cookie jar file
        :param insecure: don't check server certificate.
        :param reauthenticate: reauthenticate in case of requets failures with status code 401 or 403.
        :param login_creds: {'username': '', 'password': ''} or {'key': '', 'secret': ''}
        """
        self.endpoint = endpoint
        self.session = SessionStore(endpoint, reauthenticate, cookie_file=cookie_file,
                                    login_params=to_login_params(login_creds))
        self.session.verify = (insecure == False)
        self.session.headers.update({'Accept': 'application/xml'})
        if insecure:
            try:
                requests.packages.urllib3.disable_warnings(
                    requests.packages.urllib3.exceptions.InsecureRequestWarning)
            except:
                import urllib3
                urllib3.disable_warnings(
                    urllib3.exceptions.InsecureRequestWarning)
        self._username = None
        self._cimi_cloud_entry_point = None

    def login(self, login_params):
        """Uses given 'login_params' to log into the SlipStream server. The
        'login_params' must be a map containing an "href" element giving the id of
        the sessionTemplate resource and any other attributes required for the
        login method. E.g.:

        {"href" : "session-template/internal",
         "username" : "username",
         "password" : "password"}
         or
        {"href" : "session-template/api-key",
         "key" : "key",
         "secret" : "secret"}

        Returns server response as dict. Successful responses will contain a
        `status` code of 201 and the `resource-id` of the created session.

        :param   login_params: {"href": "session-template/...", <creds>}
        :type    login_params: dict
        :return: Server response.
        :rtype:  dict

        """
        return self.session.cimi_login(login_params)

    def login_internal(self, username, password):
        """Login to the server using username and password.

        :param username:
        :param password:
        :return: see login()
        """
        self._username = username
        return self.login(to_login_params({'username': username,
                                           'password': password}))

    def login_apikey(self, key, secret):
        """Login to the server using API key/secret pair.

        :param key: The Key ID (resource id).
                    (example: credential/ce02ef40-1342-4e68-838d-e1b2a75adb1e)
        :param secret: The Secret Key corresponding to the Key ID
        :return: see login()
        """
        return self.login(to_login_params({'key': key,
                                           'secret': secret}))

    def logout(self):
        """Logs user out by deleting session.
        """
        session_id = self.current_session()
        if session_id is not None:
            self._cimi_delete(session_id)
        self.session.login_params = None
        self._username = None

    def current_session(self):
        """Returns current user session or None.

        :return: Current user session.
        :rtype: str
        """
        resource_type = 'sessions'
        session = self.cimi_search(resource_type)
        if session and session.count > 0:
            return session.sessions[0].get('id')
        else:
            return None

    def is_authenticated(self):
        return self.current_session() is not None

    @property
    def username(self):
        if not self._username:
            session_id = self.current_session()
            if session_id:
                self._username = self.cimi_get(session_id).json.get('username')
        return self._username

    def _text_get(self, url, **params):
        response = self.session.get('%s%s' % (self.endpoint, url),
                                    headers={'Accept': 'text/plain'},
                                    params=params)
        response.raise_for_status()

        return response.text.encode('utf-8')

    def _xml_get(self, url, **params):
        response = self.session.get('%s%s' % (self.endpoint, url),
                                    headers={'Accept': 'application/xml'},
                                    params=params)
        response.raise_for_status()

        parser = etree.XMLParser(encoding='utf-8')
        parser.feed(response.text.encode('utf-8'))
        return parser.close()

    def _xml_put(self, url, data):
        return self.session.put('%s%s' % (self.endpoint, url),
                                headers={'Accept': 'application/xml',
                                         'Content-Type': 'application/xml'},
                                data=data)

    def _get_user_xml(self, username):
        if not username:
            username = self.username

        try:
            return self._xml_get('/user/%s' % username)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for user: {0}.")
            raise

    def _list_users_xml(self):
        try:
            return self._xml_get('/users')
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for users.")
            raise

    @staticmethod
    def _add_to_dict_if_not_none(d, key, value):
        if key is not None and value is not None:
            d[key] = value

    @staticmethod
    def _dict_values_to_string(d):
        return dict([(k, v) if isinstance(v, six.string_types) else str(v) for k, v in six.iteritems(d)])

    @staticmethod
    def _flatten_cloud_parameters(cloud_parameters):
        parameters = {}
        if cloud_parameters is not None:
            for cloud, params in six.iteritems(cloud_parameters):
                for name, value in six.iteritems(params):
                    parameters['{0}.{1}'.format(cloud, name)] = value
        return parameters

    @staticmethod
    def _create_xml_parameter_entry(name, value):
        category = name.split('.', 1)[0]
        entry_xml = etree.Element('entry')
        etree.SubElement(entry_xml, 'string').text = name
        param_xml = etree.SubElement(entry_xml, 'parameter', name=name, category=category)
        etree.SubElement(param_xml, 'value').text = value
        return entry_xml

    @staticmethod
    def _check_xml_result(response):
        if not (200 <= response.status_code < 300):
            try:
                reason = etree.fromstring(response.text).get('detail')
            except:
                pass
            else:
                raise SlipStreamError(reason)
        response.raise_for_status()

    def _cimi_get_cloud_entry_point(self):
        cep_json = self._cimi_get('cloud-entry-point')
        return models.CloudEntryPoint(cep_json)

    @property
    def cimi_cloud_entry_point(self):
        if self._cimi_cloud_entry_point is None:
            self._cimi_cloud_entry_point = self._cimi_get_cloud_entry_point()
        return self._cimi_cloud_entry_point

    @classmethod
    def _split_cimi_params(cls, params):
        cimi_params = {}
        other_params = {}
        for key, value in params.items():
            if key in cls.CIMI_PARAMETERS_NAME:
                cimi_params['$' + key] = value
            else:
                other_params[key] = value
        return cimi_params, other_params

    @staticmethod
    def _cimi_find_operation_href(cimi_resource, operation):
        operation_href = cimi_resource.operations_by_name.get(operation, {}).get('href')

        if not operation_href:
            raise KeyError("Operation '{0}' not found.".format(operation))

        return operation_href

    def _cimi_get_uri(self, resource_id=None, resource_type=None):
        if resource_id is None and resource_type is None:
            raise TypeError("You have to specify 'resource_uri' or 'resource_type'.")

        if resource_id is not None and resource_type is not None:
            raise TypeError("You can only specify 'resource_uri' or 'resource_type', not both.")

        if resource_type is not None:
            resource_id = self.cimi_cloud_entry_point.entry_points.get(resource_type)
            if resource_id is None:
                raise KeyError("Resource type '{0}' not found.".format(resource_type))

        return resource_id

    def _cimi_request(self, method, uri, params=None, json=None, data=None):
        response = self.session.request(method, '{0}/{1}/{2}'.format(self.endpoint, 'api', uri),
                                        headers={'Accept': 'application/json'},
                                        params=params,
                                        json=json,
                                        data=data)
        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                json_msg = e.response.json()
                message = json_msg.get('message')
                if message is None:
                    error = json_msg.get('error')
                    message = error.get('code') + ' - ' + error.get('reason')
            except:
                try:
                    message = e.response.text
                except:
                    message = str(e)
            raise SlipStreamError(message, response)

        return response.json()

    def _cimi_get(self, resource_id=None, resource_type=None, params=None):
        uri = self._cimi_get_uri(resource_id, resource_type)
        return self._cimi_request('GET', uri, params=params)

    def _cimi_post(self, resource_id=None, resource_type=None, params=None, json=None, data=None):
        uri = self._cimi_get_uri(resource_id, resource_type)
        return self._cimi_request('POST', uri, params=params, json=json, data=data)

    def _cimi_put(self, resource_id=None, resource_type=None, params=None, json=None, data=None):
        uri = self._cimi_get_uri(resource_id, resource_type)
        return self._cimi_request('PUT', uri, params=params, json=json, data=data)

    def _cimi_delete(self, resource_id=None):
        return self._cimi_request('DELETE', resource_id)

    def cimi_get(self, resource_id, **kwargs):
        """ Retreive a CIMI resource by it's resource id

        :param      resource_id: The id of the resource to retrieve
        :type       resource_id: str
        
        :keyword    select: Select attributes to return. (resourceURI always returned)
        :type       select: str or list of str

        :return:    A CimiResource object corresponding to the resource
        :rtype:     CimiResource
        """
        cimi_params, query_params = self._split_cimi_params(kwargs)
        resp_json = self._cimi_get(resource_id=resource_id, params=cimi_params)
        return models.CimiResource(resp_json)

    def cimi_edit(self, resource_id, data, **kwargs):
        """ Edit a CIMI resource by it's resource id

        :param      resource_id: The id of the resource to edit
        :type       resource_id: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :keyword    select: Cimi select parameter, used to delete an existing attribute from a cimi resource when the
                    selected fields are not present in the data argument (e.g description, value)
        :type       select: str or list of str

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse
        """
        resource = self.cimi_get(resource_id=resource_id)
        operation_href = self._cimi_find_operation_href(resource, 'edit')
        cimi_params, query_params = self._split_cimi_params(kwargs)
        return models.CimiResponse(self._cimi_put(resource_id=operation_href, json=data, params=cimi_params))

    def cimi_delete(self, resource_id):
        """ Delete a CIMI resource by it's resource id
         
        :param  resource_id: The id of the resource to delete
        :type   resource_id: str

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse
        
        """
        resource = self.cimi_get(resource_id=resource_id)
        operation_href = self._cimi_find_operation_href(resource, 'delete')
        return models.CimiResponse(self._cimi_delete(resource_id=operation_href))

    def cimi_add(self, resource_type, data):
        """ Add a CIMI resource to the specified resource_type (Collection)

        :param      resource_type: Type of the resource (Collection name)
        :type       resource_type: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse
        """
        collection = self.cimi_search(resource_type=resource_type, last=0)
        operation_href = self._cimi_find_operation_href(collection, 'add')
        return models.CimiResponse(self._cimi_post(resource_id=operation_href, json=data))

    def cimi_search(self, resource_type, **kwargs):
        """ Search for CIMI resources of the given type (Collection).

        :param      resource_type: Type of the resource (Collection name)
        :type       resource_type: str

        :keyword    first: Start from the 'first' element (1-based)
        :type       first: int

        :keyword    last: Stop at the 'last' element (1-based)
        :type       last: int

        :keyword    filter: CIMI filter
        :type       filter: str

        :keyword    select: Select attributes to return. (resourceURI always returned)
        :type       select: str or list of str

        :keyword    expand: Expand linked resources (not implemented yet)
        :type       expand: str or list of str

        :keyword    orderby: Sort by the specified attribute
        :type       orderby: str or list of str

        :keyword    aggregation: CIMI aggregation
        :type       aggregation: str (operator:field)

        :return:    A CimiCollection object with the list of found resources available
                    as a generator with the method 'resources()' or with the attribute 'resources_list'
        :rtype:     CimiCollection
        """
        cimi_params, query_params = self._split_cimi_params(kwargs)
        resp_json = self._cimi_put(resource_type=resource_type, data=cimi_params, params=query_params)
        return models.CimiCollection(resp_json, resource_type)

    def cimi_operation(self, resource_id, operation, data=None):
        """ Execute an operation on a CIMI resource

        :param      resource_id: The id of the resource to execute operation on
        :type       resource_id: str

        :param      operation: Operation name (e.g. describe)
        :type       operation: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse
        """
        resource = self.cimi_get(resource_id=resource_id)
        operation_href = self._cimi_find_operation_href(resource, operation)
        resp_json = self._cimi_post(operation_href, json=data)
        return models.CimiResource(resp_json)

    def create_user(self, username, password, email, first_name, last_name,
                    organization=None, roles=None, privileged=False,
                    default_cloud=None, default_keep_running='never',
                    ssh_public_keys=None, log_verbosity=1, execution_timeout=30,
                    usage_email='never', cloud_parameters=None):
        """
        Create a new user into SlipStream.

        :param username: The user's username (need to be unique)
        :type username: str
        :param password: The user's password
        :type password: str
        :param email: The user's email address
        :type email: str
        :param first_name: The user's first name
        :type first_name: str
        :param last_name: The user's last name
        :type last_name: str
        :param organization: The user's organization/company
        :type organization: str|None
        :param roles: The user's roles
        :type roles: list
        :param privileged: true to create a privileged user, false otherwise
        :type privileged: bool
        :param default_cloud: The user's default Cloud
        :type default_cloud: str|None
        :param default_keep_running: The user's default setting for keep-running.
        :type default_keep_running: 'always' or 'never' or 'on-success' or 'on-error'
        :param ssh_public_keys: The SSH public keys to inject into deployed instances.
                                One key per line.
        :type ssh_public_keys: str|None
        :param log_verbosity: The verbosity level of the logging inside instances.
                              0: Actions, 1: Steps, 2: Details, 3: Debugging
        :type log_verbosity: 0 or 1 or 2 or 3
        :param execution_timeout: If a deployment stays in a transitionnal state
                                  for more than this value (in minutes) it will
                                  be forcefully terminated.
        :type execution_timeout: int
        :param usage_email: Set it to 'daily' if you want to receive daily email
                            with a summary of your Cloud usage of the previous day.
        :type usage_email: 'never' or 'daily'
        :param cloud_parameters: To add Cloud specific parameters (like credentials).
                                 A dict with the cloud name as the key and a dict of parameter as the value.
        :type cloud_parameters: dict|None

        """

        attrib = dict(name=username, password=password, email=email,
                      firstName=first_name, lastName=last_name,
                      issuper=privileged,
                      state='ACTIVE', resourceUri='user/{0}'.format(username))
        self._add_to_dict_if_not_none(attrib, 'organization', organization)
        self._add_to_dict_if_not_none(attrib, 'roles', roles)
        _attrib = self._dict_values_to_string(attrib)

        parameters = self._flatten_cloud_parameters(cloud_parameters)

        self._add_to_dict_if_not_none(parameters, 'General.default.cloud.service', default_cloud)
        self._add_to_dict_if_not_none(parameters, 'General.keep-running', default_keep_running)
        self._add_to_dict_if_not_none(parameters, 'General.Verbosity Level', log_verbosity)
        self._add_to_dict_if_not_none(parameters, 'General.Timeout', execution_timeout)
        self._add_to_dict_if_not_none(parameters, 'General.mail-usage', usage_email)
        self._add_to_dict_if_not_none(parameters, 'General.ssh.public.key', ssh_public_keys)

        _parameters = self._dict_values_to_string(parameters)

        user_xml = etree.Element('user', **_attrib)

        params_xml = etree.SubElement(user_xml, 'parameters')
        for name, value in six.iteritems(_parameters):
            params_xml.append(self._create_xml_parameter_entry(name, value))

        response = self._xml_put('/user/{0}'.format(username), etree.tostring(user_xml, 'UTF-8'))

        self._check_xml_result(response)

        return True

    def update_user(self, username=None,
                    password=None, email=None, first_name=None, last_name=None,
                    organization=None, roles=None, privileged=None,
                    default_cloud=None, default_keep_running=None,
                    ssh_public_keys=None, log_verbosity=None, execution_timeout=None,
                    usage_email=None, cloud_parameters=None):
        """
        Update an existing user in SlipStream.
        Any parameter provided will be updated, others parameters will not be touched.

        Parameters are identical to the ones of the method 'create_user' except that they can all be None.

        Username cannot be updated.
        This parameter define which user to update.
        If not provided or None the current user will be used
        """
        root = self._get_user_xml(username)

        if 'roles' in root.attrib and not self.get_user().privileged:
            del root.attrib['roles']

        attrib = {}
        self._add_to_dict_if_not_none(attrib, 'email', email)
        self._add_to_dict_if_not_none(attrib, 'roles', roles)
        self._add_to_dict_if_not_none(attrib, 'password', password)
        self._add_to_dict_if_not_none(attrib, 'issuper', privileged)
        self._add_to_dict_if_not_none(attrib, 'lastName', last_name)
        self._add_to_dict_if_not_none(attrib, 'firstName', first_name)
        self._add_to_dict_if_not_none(attrib, 'organization', organization)
        _attrib = self._dict_values_to_string(attrib)

        parameters = self._flatten_cloud_parameters(cloud_parameters)
        self._add_to_dict_if_not_none(parameters, 'General.default.cloud.service', default_cloud)
        self._add_to_dict_if_not_none(parameters, 'General.keep-running', default_keep_running)
        self._add_to_dict_if_not_none(parameters, 'General.Verbosity Level', log_verbosity)
        self._add_to_dict_if_not_none(parameters, 'General.Timeout', execution_timeout)
        self._add_to_dict_if_not_none(parameters, 'General.mail-usage', usage_email)
        self._add_to_dict_if_not_none(parameters, 'General.ssh.public.key', ssh_public_keys)
        _parameters = self._dict_values_to_string(parameters)

        for key, val in six.iteritems(_attrib):
            root.set(key, val)

        for key, val in six.iteritems(_parameters):
            param_xml = root.find('parameters/entry/parameter[@name="' + key + '"]')
            if param_xml is None:
                param_entry_xml = self._create_xml_parameter_entry(key, val)
                param_xml = param_entry_xml.find('parameter')
                root.find('parameters').append(param_entry_xml)

            value_xml = param_xml.find('value')
            if value_xml is None:
                value_xml = etree.SubElement(param_xml, 'value')
            value_xml.text = val

        parameters_xml = root.find('parameters')
        for entry in parameters_xml.findall('entry'):
            param = entry.find('parameter[@name="General.orchestrator.publicsshkey"]')
            if param:
                parameters_xml.remove(entry)

        response = self._xml_put('/user/{0}'.format(root.get('name')), etree.tostring(root, 'UTF-8'))

        self._check_xml_result(response)

        return True

    def get_user(self, username=None):
        """
        Get informations for a given user, if permitted

        :param username: The username of the user.
                         Default to the user logged in if not provided or None.
        """
        root = self._get_user_xml(username)

        general_params = {}
        with_username = set()
        with_password = set()

        for p in root.findall('parameters/entry/parameter'):
            name = p.get('name', '')
            value = p.findtext('value', '')
            category = p.get('category', '')

            if (name.endswith('.username') or name.endswith('.access.id')) and value:
                with_username.add(category)
            elif (name.endswith('.password') or name.endswith('.secret.key')) and value:
                with_password.add(category)
            elif category == 'General':
                general_params[name] = value

        configured_clouds = with_username & with_password

        user = models.User(
            username=root.get('name'),
            cyclone_login=root.get('cycloneLogin'),
            github_login=root.get('githubLogin'),
            email=root.get('email'),
            first_name=root.get('firstName'),
            last_name=root.get('lastName'),
            organization=root.get('organization'),
            roles=root.get('roles', '').split(','),
            configured_clouds=configured_clouds,
            default_cloud=general_params.get('General.default.cloud.service'),
            ssh_public_keys=general_params.get('General.ssh.public.key', '').splitlines(),
            keep_running=general_params.get('General.keep-running'),
            timeout=general_params.get('General.Timeout'),
            privileged=root.get('issuper', "false").lower() == "true",
            active_since=root.get('activeSince'),
            last_online=root.get('lastOnline'),
            online=root.get('online'))

        return user

    def list_users(self):
        """
        List users (requires privileged access)
        """
        root = self._list_users_xml()
        for elem in element_tree__iter(root)('item'):
            yield models.UserItem(username=elem.get('name'),
                                  email=elem.get('email'),
                                  first_name=elem.get('firstName'),
                                  last_name=elem.get('lastName'),
                                  organization=elem.get('organization'),
                                  roles=elem.get('roles', '').split(','),
                                  privileged=elem.get('issuper', "false").lower() == "true",
                                  active_since=elem.get('activeSince'),
                                  last_online=elem.get('lastOnline'),
                                  online=elem.get('online'))

    def list_applications(self):
        """
        List apps in the appstore
        """
        root = self._xml_get('/appstore')
        for elem in element_tree__iter(root)('item'):
            yield models.App(name=elem.get('name'),
                             type=get_module_type(elem.get('category')),
                             version=int(elem.get('version')),
                             path=_mod(elem.get('resourceUri'),
                                       with_version=False))

    def get_element(self, path):
        """
        Get details about a project, a component or an application

        :param path: The path of an element (project/component/application)
        :type path: str

        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise

        ss_module = models.Module(name=root.get('shortName'),
                                  type=get_module_type(root.get('category')),
                                  created=root.get('creation'),
                                  modified=root.get('lastModified'),
                                  description=root.get('description'),
                                  version=int(root.get('version')),
                                  path=_mod('%s/%s' % (root.get('parentUri').strip('/'),
                                                       root.get('shortName'))))
        return ss_module

    def update_component(self, path, description=None, module_reference_uri=None, cloud_identifiers=None,
                         keep_ref_uri_and_cloud_ids=False, logo_link=None):
        """
        Update a component, when a parameter is not provided in parameter it is unchanged.

        :param path: The path of a component
        :type path: str
        :param description: Description of the component
        :type description: str
        :param module_reference_uri: URI of the parent component
        :type module_reference_uri: str
        :param cloud_identifiers: A dict where keys are cloud names and values are identifier of the image in the cloud
        :type cloud_identifiers: dict
        :param keep_ref_uri_and_cloud_ids: Don't remove module_reference_uri if any cloud identifier are provided,
                                           or don't remove cloud identifiers if a module_reference_uri is provided
        :type keep_ref_uri_and_cloud_ids: bool
        :param logo_link: URL to an image that should be used as logo
        :type logo_link: str

        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise
        if str(root.get('category')) != "Image":
            raise SlipStreamError("Specified path is not a component")

        if description is not None:
            root.set('description', description)

        if logo_link is not None:
            root.set('logoLink', logo_link)

        if module_reference_uri is not None:
            root.set('moduleReferenceUri', module_reference_uri)
            if not keep_ref_uri_and_cloud_ids:
                root.set('isBase', 'false')
                root.find('cloudImageIdentifiers').clear()

        if cloud_identifiers is not None:
            cloud_image_identifiers = root.find('cloudImageIdentifiers')
            for cloud, identifier in cloud_identifiers.items():
                node = cloud_image_identifiers.find('cloudImageIdentifier[@cloudServiceName="%s"]' % cloud)
                if identifier is None or len(identifier) == 0:
                    if node is not None:
                        cloud_image_identifiers.remove(node)
                else:
                    if node is None:
                        node = etree.Element('cloudImageIdentifier', cloudServiceName=cloud)
                        cloud_image_identifiers.append(node)
                    node.set('cloudImageIdentifier', identifier)
            if not keep_ref_uri_and_cloud_ids:
                root.set('moduleReferenceUri', '')
                root.set('isBase', 'true')

        try:
            self._xml_put(url, etree.tostring(root, 'UTF-8'))
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise

    def get_cloud_image_identifiers(self, path):
        """
        Get all image identifiers associated to a native component

        :param path: The path of an component
        :type path: str

        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise

        for node in root.findall("cloudImageIdentifiers/cloudImageIdentifier"):
            yield models.CloudImageIdentifier(
                cloud=node.get("cloudServiceName"),
                identifier=node.get("cloudImageIdentifier"),
            )

    def get_application_nodes(self, path):
        """
        Get nodes of an application
        :param path: The path of an application
        :type path: str
        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise
        for node in root.findall("nodes/entry/node"):
            yield models.Node(path=_mod(node.get("imageUri")),
                              name=node.get('name'),
                              cloud=node.get('cloudService'),
                              multiplicity=node.get('multiplicity'),
                              max_provisioning_failures=node.get('maxProvisioningFailures'),
                              network=node.get('network'),
                              cpu=node.get('cpu'),
                              ram=node.get('ram'),
                              disk=node.get('disk'),
                              extra_disk_volatile=node.get('extraDiskVolatile'),
                              )

    def get_parameters(self, path, parameter_name=None, parameter_names=None):
        """
        Get all or a subset of the parameters associated to a project, a component or an application

        :param path: The path of an  element (project/component/application)
        :type path: str

        :param parameter_name: The parameter name (eg: 'cpu.nb')
        :type parameter_name: str|None

        :param parameter_names: The list of parameter names (eg: ['cpu.nb', 'ram.GB', ])
        :type parameter_names: list|None

        :return: A list containing all the parameters, or at most the one requested
        :rtype: list

        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise

        if parameter_name is not None:
            query = 'parameters/entry/parameter[@name="' + parameter_name + '"]'
        else:
            query = 'parameters/entry/parameter'

        for node in root.findall(query):
            value = node.findtext('value', '')
            defaultValue = node.findtext('defaultValue', '')
            instructions = node.findtext('instructions', '')
            name = node.get("name")
            if parameter_names is None or name in parameter_names:
                yield models.ModuleParameter(
                    name=name,
                    value=value,
                    defaultValue=defaultValue,
                    category=node.get("category"),
                    description=node.get("description"),
                    isSet=node.get("isSet"),
                    mandatory=node.get("mandatory"),
                    readonly=node.get("readonly"),
                    type=node.get("type"),
                    instructions=instructions,
                )

    def list_project_content(self, path=None, recurse=False):
        """
        List the content of a project

        :param path: The path of a project. If None, list the root project.
        :type path: str
        :param recurse: Get project content recursively
        :type recurse: bool

        """
        logger.debug("Starting with path: {0}".format(path))
        # Path normalization
        if not path:
            url = '/module'
        else:
            url = _mod_url(path)
        logger.debug("Using normalized URL: {0}".format(url))

        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
                return
            raise

        for elem in element_tree__iter(root)('item'):
            # Compute module path
            if elem.get('resourceUri'):
                app_path = elem.get('resourceUri')
            else:
                app_path = "%s/%s" % (root.get('parentUri').strip('/'),
                                      '/'.join([root.get('shortName'),
                                                elem.get('name'),
                                                elem.get('version')]))

            module_type = get_module_type(elem.get('category'))
            logger.debug("Found '{0}' with path: {1}".format(module_type, app_path))
            app = models.App(name=elem.get('name'),
                             type=module_type,
                             version=int(elem.get('version')),
                             path=_mod(app_path, with_version=False))
            yield app
            if app.type == 'project' and recurse:
                logger.debug("Recursing into path: {0}".format(app_path))
                for app in self.list_project_content(app_path, recurse):
                    yield app

    def list_deployments(self, inactive=False, cloud=None, offset=0, limit=20):
        """
        List deployments

        :param inactive: Include inactive deployments. Default to False
        :type cloud: bool

        :param cloud: Retrieve only deployments for the specified Cloud
        :type cloud: str

        :param offset: Retrieve deployments starting by the offset<exp>th</exp> one. Default to 0
        :type offset: int

        :param limit: Retrieve at most 'limit' deployments. Default to 20
        :type limit: int

        """
        _cloud = ''
        if cloud is not None:
            _cloud = cloud

        root = self._xml_get('/run', activeOnly=(not inactive), offset=offset, limit=limit, cloud=_cloud)
        for elem in element_tree__iter(root)('item'):
            yield models.Deployment(id=uuid.UUID(elem.get('uuid')),
                                    module=_mod(elem.get('moduleResourceUri')),
                                    status=elem.get('status').lower(),
                                    started_at=elem.get('startTime'),
                                    last_state_change=elem.get('lastStateChangeTime'),
                                    clouds=elem.get('cloudServiceNames', '').split(','),
                                    username=elem.get('username'),
                                    abort=elem.get('abort'),
                                    service_url=elem.get('serviceUrl'),
                                    scalable=elem.get('mutable'),
                                    )

    def get_deployment(self, deployment_id):
        """
        Get a deployment

        :param deployment_id: The deployment UUID of the deployment to get
        :type deployment_id: str or UUID

        """
        root = self._xml_get('/run/' + str(deployment_id))

        abort = root.findtext('runtimeParameters/entry/runtimeParameter[@key="ss:abort"]')
        service_url = root.findtext('runtimeParameters/entry/runtimeParameter[@key="ss:url.service"]')

        return models.Deployment(id=uuid.UUID(root.get('uuid')),
                                 module=_mod(root.get('moduleResourceUri')),
                                 status=root.get('state').lower(),
                                 started_at=root.get('startTime'),
                                 last_state_change=root.get('lastStateChangeTime'),
                                 clouds=root.get('cloudServiceNames', '').split(','),
                                 username=root.get('user'),
                                 abort=abort,
                                 service_url=service_url,
                                 scalable=root.get('mutable'),
                                 )

    def get_deployment_parameter(self, deployment_id, parameter_name, ignore_abort=False):
        """
        Get a parameter of a deployment
        
        :param deployment_id: The deployment UUID of the deployment to get
        :type deployment_id: str or UUID
        
        :param parameter_name: The parameter name (eg: ss:state)
        :type parameter_name: str
        
        :param ignore_abort: If False, raise an exception if the deployment has failed
        :type ignore_abort: bool
        """
        ignoreabort = str(ignore_abort).lower()
        return self._text_get('/run/{0}/{1}'.format(str(deployment_id), parameter_name),
                              ignoreabort=ignoreabort)

    def get_deployment_events(self, deployment_id, types=None):
        if types is None:
            types = []
        filter = "content/resource/href='run/%s'" % deployment_id
        if types:
            filter += " and (%s)" % ' or '.join(map(lambda x: "type='%s'" % x, types))
        return self.cimi_search(resource_type='events', filter=filter)

    def list_virtualmachines(self, deployment_id=None, cloud=None, offset=0, limit=20):
        """
        List virtual machines

        :param deployment_id: Retrieve only virtual machines about the specified run_id. Default to None
        :type deployment_id: str or UUID

        :param cloud: Retrieve only virtual machines for the specified Cloud
        :type cloud: str

        :param offset: Retrieve virtual machines starting by the offset<exp>th</exp> one. Default to 0
        :type offset: int

        :param limit: Retrieve at most 'limit' virtual machines. Default to 20
        :type limit: int
        """
        _deployment_id = ''
        if deployment_id is not None:
            _deployment_id = str(deployment_id)

        _cloud = ''
        if cloud is not None:
            _cloud = cloud

        root = self._xml_get('/vms', offset=offset, limit=limit, runUuid=_deployment_id, cloud=_cloud)
        for elem in element_tree__iter(root)('vm'):
            run_id_str = elem.get('runUuid')
            run_id = uuid.UUID(run_id_str) if run_id_str is not None else None
            yield models.VirtualMachine(id=elem.get('instanceId'),
                                        cloud=elem.get('cloud'),
                                        status=elem.get('state').lower(),
                                        deployment_id=run_id,
                                        deployment_owner=elem.get('runOwner'),
                                        node_name=elem.get('nodeName'),
                                        node_instance_id=elem.get('nodeInstanceId'),
                                        ip=elem.get('ip'),
                                        cpu=elem.get('cpu'),
                                        ram=elem.get('ram'),
                                        disk=elem.get('disk'),
                                        instance_type=elem.get('instanceType'),
                                        is_usable=elem.get('isUsable'))

    def build_component(self, path, cloud=None):
        """

        :param path: The path to a component
        :type path: str
        :param cloud: The Cloud on which to build the component. If None, the user default Cloud will be used.
        :type cloud: str

        """
        response = self.session.post(self.endpoint + '/run', data={
            'type': 'Machine',
            'refqname': path,
            'parameter--cloudservice': cloud or 'default',
        })
        response.raise_for_status()
        run_id = response.headers['location'].split('/')[-1]
        return uuid.UUID(run_id)

    def deploy(self, path, cloud=None, parameters=None, tags=None, keep_running=None, scalable=False, multiplicity=None,
               tolerate_failures=None, check_ssh_key=False, raw_params=None):
        """
        Run a component or an application

        :param path: The path of the component/application to deploy
        :type path: str
        :param cloud: A string or a dict to specify on which Cloud(s) to deploy the component/application.
                      To deploy a component simply specify the Cloud name as a string.
                      To deploy a deployment specify a dict with the nodenames as keys and Cloud names as values.
                      If not specified the user default cloud will be used.
        :type cloud: str or dict
        :param parameters: A dict of parameters to redefine for this deployment.
                           To redefine a parameter of a node use "<nodename>" as keys and dict of parameters as values.
                           To redefine a parameter of a component or a global parameter use "<parametername>" as the key.
        :type parameters: dict
        :param tags: List of tags that can be used to identify or annotate a deployment
        :type tags: str or list
        :param keep_running: [Only applies to applications] Define when to terminate or not a deployment when it reach the
                             'Ready' state. Possibles values: 'always', 'never', 'on-success', 'on-error'.
                             If scalable is set to True, this value is ignored and it will behave as if it was set to 'always'.
                             If not specified the user default will be used.
        :type keep_running: 'always' or 'never' or 'on-success' or 'on-error'
        :param scalable: [Only applies to applications] True to start a scalable deployment. Default: False
        :type scalable: bool
        :param multiplicity: [Only applies to applications] A dict to specify how many instances to start per node.
                             Nodenames as keys and number of instances to start as values.
        :type multiplicity: dict
        :param tolerate_failures: [Only applies to applications] A dict to specify how many failures to tolerate per node.
                                  Nodenames as keys and number of failure to tolerate as values.
        :type tolerate_failures: dict
        :param check_ssh_key: Set it to True if you want the SlipStream server to check if you have a public ssh key
                              defined in your user profile. Useful if you want to ensure you will have access to VMs.
        :type check_ssh_key: bool
        :param raw_params: This allows you to pass parameters directly in the request to the SlipStream server.
                           Keys must be formatted in the format understood by the SlipStream server.
        :type raw_params: dict

        :return: The deployment UUID of the newly created deployment
        :rtype: uuid.UUID
        """

        _raw_params = dict() if raw_params is None else raw_params
        _raw_params.update(self._convert_parameters_to_raw_params(parameters))
        _raw_params.update(self._convert_clouds_to_raw_params(cloud))
        _raw_params.update(self._convert_multiplicity_to_raw_params(multiplicity))
        _raw_params.update(self._convert_tolerate_failures_to_raw_params(tolerate_failures))
        _raw_params['refqname'] = _mod_url(path)[1:]

        if tags:
            _raw_params['tags'] = tags if isinstance(tags, six.string_types) else ','.join(tags)

        if keep_running:
            if keep_running not in self.KEEP_RUNNING_VALUES:
                raise ValueError('"keep_running" should be one of {0}, not "{1}"'.format(self.KEEP_RUNNING_VALUES,
                                                                                         keep_running))
            _raw_params['keep-running'] = keep_running

        if scalable:
            _raw_params['mutable'] = 'on'

        if not check_ssh_key:
            _raw_params['bypass-ssh-check'] = 'true'

        response = self.session.post(self.endpoint + '/run', data=_raw_params)

        if response.status_code == 409:
            reason = etree.fromstring(response.text).get('detail')
            raise SlipStreamError(reason)

        response.raise_for_status()
        deployment_id = response.headers['location'].split('/')[-1]
        return uuid.UUID(deployment_id)

    def terminate(self, deployment_id):
        """
        Terminate a deployment

        :param deployment_id: The UUID of the deployment to terminate
        :type deployment_id: str or uuid.UUID

        """
        response = self.session.delete('%s/run/%s' % (self.endpoint, deployment_id))
        response.raise_for_status()
        return True

    def add_node_instances(self, deployment_id, node_name, quantity=None):
        """
        Add new instance(s) of a deployment's node (horizontal scale up).
        
        Warning: The targeted deployment has to be "scalable".

        :param deployment_id: The deployment UUID of the deployment on which to add new instances of a node.
        :type deployment_id: str|UUID
        :param node_name: Name of the node where to add instances.
        :type node_name: str
        :param quantity: Amount of node instances to add. If not provided it's server dependent (usually add one instance)
        :type quantity: int

        :return: The list of new node instance names.
        :rtype: list

        """
        url = '%s/run/%s/%s' % (self.endpoint, str(deployment_id), str(node_name))
        data = {"n": quantity} if quantity else None

        response = self.session.post(url, data=data)

        if response.status_code == 409:
            reason = etree.fromstring(response.text).get('detail')
            raise SlipStreamError(reason)

        response.raise_for_status()

        return response.text.split(",")

    def remove_node_instances(self, deployment_id, node_name, ids):
        """
        Remove a list of node instances from a deployment.
        
        Warning: The targeted deployment has to be "scalable".

        :param deployment_id: The deployment UUID of the deployment on which to remove instances of a node.
        :type deployment_id: str|UUID
        :param node_name: Name of the node where to remove instances.
        :type node_name: str
        :param ids: List of node instance ids to remove. Ids can also be provided as a CSV list.
        :type ids: list|str

        :return: True on success
        :rtype: bool

        """
        url = '%s/run/%s/%s' % (self.endpoint, str(deployment_id), str(node_name))

        response = self.session.delete(url, data={"ids": ",".join(str(id_) for id_ in ids)})

        if response.status_code == 409:
            reason = etree.fromstring(response.text).get('detail')
            raise SlipStreamError(reason)

        response.raise_for_status()

        return response.status_code == 204

    def usage(self):
        """
        Get current usage and quota by cloud service.
        """
        root = self._xml_get('/dashboard')
        for elem in element_tree__iter(root)('cloudUsage'):
            yield models.Usage(cloud=elem.get('cloud'),
                               quota=int(elem.get('vmQuota')),
                               run_usage=int(elem.get('userRunUsage')),
                               vm_usage=int(elem.get('userVmUsage')),
                               inactive_vm_usage=int(elem.get('userInactiveVmUsage')),
                               others_vm_usage=int(elem.get('othersVmUsage')),
                               pending_vm_usage=int(elem.get('pendingVmUsage')),
                               unknown_vm_usage=int(elem.get('unknownVmUsage')))

    def publish(self, path):
        """
        Publish a component or an application to the appstore

        :param path: The path to a component or an application

        """
        response = self.session.put('%s%s/publish' % (self.endpoint,
                                                      _mod_url(path)))
        response.raise_for_status()
        return True

    def unpublish(self, path):
        """
        Unpublish a component or an application from the appstore

        :param path: The path to a component or an application

        """
        response = self.session.delete('%s%s/publish' % (self.endpoint,
                                                         _mod_url(path)))
        response.raise_for_status()
        return True

    def delete_element(self, path):
        """
        Delete a project, a component or an application

        :param path: The path to a component or an application

        """
        response = self.session.delete('%s%s' % (self.endpoint, _mod_url(path)))

        response.raise_for_status()
        return True

    @staticmethod
    def _check_type(obj_name, obj, allowed_types):
        if not isinstance(obj, allowed_types):
            raise ValueError('Invalid type "{0}" for "{1}"'.format(type(obj), obj_name))

    @classmethod
    def _convert_clouds_to_raw_params(cls, clouds):
        return cls._convert_per_node_parameter_to_raw_params('cloudservice', clouds, allowed_types=string_types)

    @classmethod
    def _convert_multiplicity_to_raw_params(cls, multiplicity):
        return cls._convert_per_node_parameter_to_raw_params('multiplicity', multiplicity,
                                                             allowed_types=(integer_types, string_types))

    @classmethod
    def _convert_tolerate_failures_to_raw_params(cls, tolerate_failures):
        return cls._convert_per_node_parameter_to_raw_params('max-provisioning-failures', tolerate_failures,
                                                             allowed_types=(integer_types, string_types))

    @classmethod
    def _convert_per_node_parameter_to_raw_params(cls, parameter_name, parameters, allowed_types=(string_types, int),
                                                  allow_no_node=True):
        raw_params = dict()

        if parameters is None:
            return raw_params

        if isinstance(parameters, dict):
            for key, value in parameters.items():
                cls._check_type('{0}:{1}'.format(key, parameter_name), value, allowed_types)
                raw_params['parameter--node--{0}--{1}'.format(key, parameter_name)] = value
        elif allow_no_node:
            cls._check_type(parameter_name, parameters, allowed_types)
            raw_params['parameter--{0}'.format(parameter_name)] = parameters
        else:
            cls._check_type(parameter_name, parameters, dict)

        return raw_params

    @classmethod
    def _convert_parameters_to_raw_params(cls, parameters):
        raw_params = dict()

        if parameters is None:
            return raw_params

        for key, value in parameters.items():
            if isinstance(value, dict):
                # Redefine node parameters
                for parameter_name, parameter_value in value.items():
                    raw_params['parameter--node--{0}--{1}'.format(key, parameter_name)] = parameter_value
            else:
                if key in cls.GLOBAL_PARAMETERS:
                    # Redefine a global parameter
                    raw_params[key] = value
                else:
                    # Redefine a component parameter
                    raw_params['parameter--{0}'.format(key)] = value

        return raw_params

    def get_cloud_credentials(self, cimi_filter=''):
        filter = "type^='cloud-cred'"
        if cimi_filter:
            filter += 'and %s' % cimi_filter
        return self.cimi_search(resource_type='credentials', filter=filter)
