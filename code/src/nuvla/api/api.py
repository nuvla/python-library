# -*- coding: utf-8 -*-

"""
 Python wrapper of the Nuvla API.


 Install
 -------

 Latest release from pypi
 ~~~~~~~~~~~~~~~~~~~~~~~~
 .. code-block:: Bash

   $ pip install nuvla-api

 Most recent version from source code
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 .. code-block:: Bash

   $ pip install 'https://github.com/nuvla/python-api/archive/master.zip'


 Usage
 -----
 To use this library, import it and instantiate it.
 Then use one of the method to login.::
    from nuvla.api import Api

    api = Api()

    api.login_password('username', 'password')


 Examples
 --------

 Login on Nuvla with username and password
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    api.login_password('username', 'password')


 Login on Nuvla with key and secret
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 ::

    api.login_apikey('credential/ce02ef40-1342-4e68-838d-e1b2a75adb1e',
                     'the-secret-key')


 API documentation
 -----------------

"""

import json as jsonlib
import logging
import os
import stat
import copy
import gzip
from typing import Optional

import requests
from requests.cookies import MockRequest
from requests.exceptions import HTTPError, ConnectionError
from http.cookiejar import MozillaCookieJar
from urllib.parse import urlparse

from .models import CimiResource, CimiCollection, CimiResponse, CloudEntryPoint

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120
DEFAULT_ENDPOINT = 'https://nuvla.io'
DEFAULT_COOKIE_FILE = os.path.expanduser('~/.nuvla/cookies.txt')
HREF_SESSION_TMPL_PASSWORD = 'session-template/password'
HREF_SESSION_TMPL_APIKEY = 'session-template/api-key'
CLOUD_ENTRY_POINT_ID = 'cloud-entry-point'
APPLICATION_JSON = 'application/json'


class NuvlaError(Exception):
    def __init__(self, reason, response: Optional[requests.Response] = None):
        super(NuvlaError, self).__init__(reason)
        self.reason = reason
        self.response = response


class NuvlaResourceOperationNotAvailable(KeyError):
    def __init__(self, reason, operation):
        super().__init__(reason)
        self.operation = operation


def _request_debug(method, endpoint, params=None, doc=None,
                   data=None, headers: Optional[dict] = None):
    # TODO: Use logging library.
    print('::: HTTP Request -> Response :::')
    print('>>> Request')
    url_res = urlparse(endpoint)
    print('{0} {1}'.format(method, url_res.path))
    print('Host: {}'.format(url_res.netloc))
    for k, v in headers.items():
        print('{0}: {1}'.format(k, v))
    if any([params, jsonlib, data]):
        print()
    if params:
        print('params:', params)
    if doc:
        print(jsonlib.dumps(doc, indent=2, sort_keys=True))
    if data:
        print('data:', data)
    print('<<< Request')


def _response_debug(response: requests.Response):
    # TODO: Use logging library.
    print('>>> Response')
    print(response.status_code, response.reason)
    for k, v in response.headers.items():
        print('{0}: {1}'.format(k, v))
    print()
    print(response.text)
    print('<<< Response')


class SessionStore(requests.Session):
    """A ``requests.Session`` subclass implementing a file-based session store."""

    def __init__(self, endpoint, persist_cookie, cookie_file, reauthenticate,
                 login_params, authn_header=None, debug=False):
        super(SessionStore, self).__init__()
        self.session_base_url = '{0}/api/session'.format(endpoint)
        self.reauthenticate = reauthenticate
        self.persist_cookie = persist_cookie
        self.login_params = login_params
        self.authn_header = authn_header
        self._debug = debug
        if persist_cookie:
            if cookie_file is None:
                cookie_file = DEFAULT_COOKIE_FILE
            cookie_dir = os.path.dirname(cookie_file)
            self.cookies = MozillaCookieJar(cookie_file)
            # Create the $HOME/.nuvla dir if it doesn't exist
            if not os.path.isdir(cookie_dir):
                os.mkdir(cookie_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            # Load existing cookies if the cookies.txt exists
            if os.path.isfile(cookie_file):
                self.cookies.load(ignore_discard=True)
                self.cookies.clear_expired_cookies()

    def need_to_login(self, accessed_url, status_code):
        return self.reauthenticate \
               and status_code in [401, 403] \
               and accessed_url != self.session_base_url

    def _request(self, *args, **kwargs):
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        if self.authn_header is not None:
            headers = kwargs.get('headers', {})
            headers['nuvla-authn-info'] = self.authn_header
            kwargs['headers'] = headers
        return super(SessionStore, self).request(*args, **kwargs)

    def request(self, *args, **kwargs):
        response = self._request(*args, **kwargs)

        if not self.verify and response.cookies:
            self._unsecure_cookie(args[1], response)
        if self.persist_cookie and 'Set-Cookie' in response.headers:
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
            method = 'POST'
            endpoint = self.session_base_url
            headers = {'Content-Type': APPLICATION_JSON,
                       'Accept': APPLICATION_JSON}
            json = {'template': login_params}
            if self._debug:
                _request_debug(method, endpoint, doc=json, headers=headers)
            response = self.request(method, endpoint, headers=headers, json=json)
            if self._debug:
                _response_debug(response)
            return response
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
            if self.persist_cookie:
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
        creds.update({'href': HREF_SESSION_TMPL_PASSWORD})
    elif ('key' in creds) and ('secret' in creds):
        creds.update({'href': HREF_SESSION_TMPL_APIKEY})
    else:
        return {}
    return creds


class Api(object):
    """ This class is a Python wrapper&helper of the native Nuvla REST API"""

    def __init__(self, endpoint=DEFAULT_ENDPOINT, insecure=False, persist_cookie=True,
                 cookie_file=None, reauthenticate=False, login_creds=None, authn_header=None,
                 debug=False, compress=False):
        """
        :param endpoint: Nuvla endpoint (https://nuvla.io).
        :param insecure: Don't check server certificate or you are using a http connection.
        The http option is strongly unrecommanded.
        :param persist_cookie: Use file to persist cookies.
        :param cookie_file: Allow to specify cookie jar file path.
        :param reauthenticate: Reauthenticate in case of requests failures with status code 401 or 403.
        :param login_creds: {'username': '', 'password': ''} or {'key': '', 'secret': ''}
        :param authn_header: String containing list of claims for authentication header
        :param compress: Compress json data sent to the server. Needs to be supported by the server.
        """
        self.endpoint = endpoint
        self.session = SessionStore(endpoint, persist_cookie, cookie_file, reauthenticate,
                                    login_params=to_login_params(login_creds),
                                    authn_header=authn_header,
                                    debug=debug)
        self.session.verify = not insecure
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
        self._debug = debug
        self._compress = compress

    def login(self, login_params):
        """Uses given 'login_params' to log into the Nuvla server. The
        'login_params' must be a map containing an "href" element giving the id of
        the session-template resource and any other attributes required for the
        login method. E.g.:

        {"href" : "session-template/password",
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
        :rtype:  requests.Response

        """
        return self.session.cimi_login(login_params)

    def login_internal(self, username, password):
        """Deprecated! Use login_password instead. This will be removed in near future.
        Login to the server using username and password.

        :param username:
        :param password:
        :return: see login()
        """
        logging.warning('Deprecated! Use instead login_password')
        return self.login(to_login_params({'username': username,
                                           'password': password}))

    def login_password(self, username, password):
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
        """Logout user by deleting his session.
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
        resource_type = 'session'
        session = self.search(resource_type)
        if session and session.count > 0:
            return session.resources[0].id
        else:
            return None

    def is_authenticated(self):
        return self.current_session() is not None

    def _cimi_get_cloud_entry_point(self):
        cep_json = self._cimi_get(CLOUD_ENTRY_POINT_ID)
        return CloudEntryPoint(cep_json)

    @property
    def cloud_entry_point(self):
        if self._cimi_cloud_entry_point is None:
            self._cimi_cloud_entry_point = self._cimi_get_cloud_entry_point()
        return self._cimi_cloud_entry_point

    @staticmethod
    def _cimi_find_operation_href(cimi_resource: CimiResource, operation: str):
        operation_href = cimi_resource.operations.get(operation, {}).get('href')

        if not operation_href:
            raise NuvlaResourceOperationNotAvailable(
                "Operation '{0}' not found.".format(operation), operation)

        return operation_href

    def _cimi_get_uri(self, resource_id=None, resource_type=None):
        if resource_id is None and resource_type is None:
            raise TypeError("You have to specify 'resource_id' or 'resource_type'.")

        if resource_id is not None and resource_type is not None:
            raise TypeError("You can only specify 'resource_id' or 'resource_type', not both.")

        if resource_type is not None:
            resource_id = self.cloud_entry_point.collections.get(resource_type)
            if resource_id is None:
                raise KeyError("Resource type '{0}' not found.".format(resource_type))

        return resource_id

    def _cimi_request(self, method, uri, params=None, json=None, data=None, headers=None):
        _headers = {'Accept': APPLICATION_JSON,
                    'Accept-Encoding': 'gzip'}

        if json and data:
            logger.warning('_cimi_request: Both "json" and "data" arguments provided. '
                           'This is unsupported and can cause unexpected behaviour.')

        if json:
            _headers['Content-Type'] = APPLICATION_JSON

        if headers:
            _headers.update(headers)

        endpoint = '{0}/{1}/{2}'.format(self.endpoint, 'api', uri)

        if self._compress and json is not None:
            data_to_compress = bytes(jsonlib.dumps(json), 'utf-8')
            data_compressed = gzip.compress(data_to_compress)

            compression_ratio = len(data_to_compress) / len(data_compressed)
            logger.debug(f'_cimi_request: Request data compression ratio: {compression_ratio:.2f} '
                        f'({len(data_to_compress)}/{len(data_compressed)} bytes)')

            if compression_ratio > 1:
                json = None
                data = data_compressed
                _headers['Content-Encoding'] = 'gzip'
            else:
                logger.debug('_cimi_request: Compressed data bigger than uncompressed data. '
                            'Sending uncompressed data.')

        if self._debug and uri != CLOUD_ENTRY_POINT_ID:
            _request_debug(method, endpoint, params, json, data, _headers)

        response = self.session.request(method, endpoint,
                                        headers=_headers,
                                        allow_redirects=False,
                                        params=params,
                                        json=json,
                                        data=data)

        if self._debug and uri != CLOUD_ENTRY_POINT_ID:
            _response_debug(response)
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
            raise NuvlaError(message, response)

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

    def get(self, resource_id, **kwargs) -> CimiResource:
        """ Retreive a CIMI resource by it's resource id

        :param      resource_id: The id of the resource to retrieve
        :type       resource_id: str

        :keyword    select: Select attributes to return. (resource-type always returned)
        :type       select: str or list of str

        :return:    A CimiResource object corresponding to the resource
        :rtype:     CimiResource
        """
        resp_json = self._cimi_get(resource_id=resource_id, params=kwargs)
        return CimiResource(resp_json)

    def edit(self, resource_id, data, **kwargs) -> CimiResource:
        """ Edit a CIMI resource by it's resource id

        :param      resource_id: The id of the resource to edit
        :type       resource_id: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :keyword    select: Cimi select parameter, used to delete an existing attribute from a cimi resource when the
                    selected fields are not present in the data argument (e.g description, value)
        :type       select: str or list of str

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResource
        """
        resource = self.get(resource_id=resource_id)
        operation_href = self._cimi_find_operation_href(resource, 'edit')
        return CimiResource(self._cimi_put(resource_id=operation_href, json=data, params=kwargs))

    def delete(self, resource_id) -> CimiResponse:
        """ Delete a CIMI resource by it's resource id

        :param  resource_id: The id of the resource to delete
        :type   resource_id: str

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse

        """
        resource = self.get(resource_id=resource_id)
        operation_href = self._cimi_find_operation_href(resource, 'delete')
        return CimiResponse(self._cimi_delete(resource_id=operation_href))

    def delete_bulk(self, resource_type, filter, **kwargs) -> CimiResponse:
        """ Bulk delete CIMI resources of the given type (Collection).

        :param      resource_type: Type of the resource (Collection name).
        :type       resource_type: str

        :param      Non-empty CIMI filter.
        :type       filter: str

        :return:    A CimiResponse object with the number of deleted records and other statistics.
        :rtype:     CimiResponse
        """
        if not isinstance(filter, str) or len(filter) == 0:
            raise NuvlaError("'filter' must be a non-empty string.")
        else:
            return CimiResponse(
                self._cimi_request('DELETE', resource_type,
                                   data={'filter': filter}, headers={'bulk': 'yes'}))

    def operation_bulk(self, resource_type, filter, operation, data=None) -> CimiResponse:
        """ Bulk delete CIMI resources of the given type (Collection).

        :param      resource_type: Type of the resource (Collection name).
        :type       resource_type: str

        :param      Non-empty CIMI filter.
        :type       filter: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id', 'message' and 'location'
        :rtype:     CimiResponse
        """
        if not isinstance(filter, str) or len(filter) == 0:
            raise NuvlaError("'filter' must be a non-empty string.")
        else:
            data_with_filter = copy.deepcopy(data)
            data_with_filter['filter'] = filter
            return CimiResponse(
                self._cimi_request('PATCH', '{0}/{1}'.format(resource_type, operation),
                                   json=data_with_filter, headers={'bulk': 'yes'}))

    def add(self, resource_type, data):
        """ Add a CIMI resource to the specified resource_type (Collection)

        :param      resource_type: Type of the resource (Collection name)
        :type       resource_type: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id' and 'message'
        :rtype:     CimiResponse
        """
        collection = self.search(resource_type=resource_type, last=0)
        operation_href = self._cimi_find_operation_href(collection, 'add')
        return CimiResponse(self._cimi_post(resource_id=operation_href, json=data))

    def search(self, resource_type, **kwargs) -> CimiCollection:
        """ Search for CIMI resources of the given type (Collection).

        :param      resource_type: Type of the resource (Collection name)
        :type       resource_type: str

        :keyword    first: Start from the 'first' element (1-based)
        :type       first: int

        :keyword    last: Stop at the 'last' element (1-based)
        :type       last: int

        :keyword    filter: CIMI filter
        :type       filter: str

        :keyword    select: Select attributes to return. (resource-type always returned)
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
        resp_json = self._cimi_put(resource_type=resource_type, data=kwargs)
        return CimiCollection(resp_json)

    def operation(self, resource: CimiResource, operation, data=None) -> CimiResponse:
        """ Execute an operation on a CIMI resource

        :param      resource: The resource to execute operation on.
        :type       resource: CimiResource

        :param      operation: Operation name (e.g. describe)
        :type       operation: str

        :param      data: The data to serialize into JSON
        :type       data: dict

        :return:    A CimiResponse object which should contain the attributes 'status', 'resource-id', 'message' and 'location'
        :rtype:     CimiResponse
        """
        operation_href = self._cimi_find_operation_href(resource, operation)
        resp_json = self._cimi_post(operation_href, json=data)
        return CimiResponse(resp_json)
