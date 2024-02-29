#!/usr/bin/env python

from nuvla.api import Api as Nuvla
from nuvla.api.resources.deployment import Deployment
from pprint import pprint as pp

debug = False
if debug:
    import requests
    import logging
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


nuvla = Nuvla(endpoint='https://localhost', insecure=True)
res = nuvla.login_password('super', 'supeR8-supeR8')
if not res.ok:
    raise Exception('Login failed: {}'.format(res.json().get('message', '')))

dpl_api = Deployment(nuvla)

module_id = 'module/20b6ea7a-ee55-44e7-93e7-7f26b4caef18'

data_records = ['data-record/36fe11cc-7f4f-4ee5-a123-0fafacf4a24b',
                'data-record/6803e2e4-1db6-42b4-8b8c-b3273c938366']
data_objects = ['data-object/36fe11cc-7f4f-4ee5-a123-0fafacf4a24b',
                'data-object/6803e2e4-1db6-42b4-8b8c-b3273c938366']
data_sets = [{'id': 'data-set/31d8ce24-7567-455e-9d39-4763c1d4010e',
              'time-start': '2020-02-14T23:00:00Z',
              'time-end': '2020-03-16T22:45:00Z'},
             {'filter': "content-type='gnss/perf-test' and gnss:station='nuvlabox-esac'",
              'data-type': 'data-object',
              'time-start': '2020-02-14T23:00:00Z',
              'time-end': '2020-03-16T22:45:00Z'}]

dpl = dpl_api.create(module_id,
                     data_sets=data_sets,
                     data_records=data_records,
                     data_objects=data_objects)

pp(dpl)

res = dpl_api.delete(dpl_api.id(dpl))
pp(res)

nuvla.logout()
