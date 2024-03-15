#!/usr/bin/env python

import time
from nuvla.api import Api as Nuvla
from nuvla.api.resources.module import Module
from nuvla.api.resources.deployment import Deployment
from nuvla.api.resources.user import User
from utils import nuvla_conf_user_pass

# Set to True to print Nuvla request / response messages to stdout.
debug = False

# Get username and password from configuration file.
username, password = nuvla_conf_user_pass()

# Create Nuvla client. No authentication required.
nuvla = Nuvla(debug=debug)
# nuvla = Nuvla(endpoint='https://localhost', insecure=True, debug=debug)

#
# Login to Nuvla.
#
user_api = User(nuvla)
user_api.login_password(username, password)

#
# Create Deployment API handler.
#
dpl_api = Deployment(nuvla)

# Define application module to start.
module_api = Module(nuvla)
app_path = 'my-first-project/jupyter'
module_id = module_api.get_by_path(app_path)['id']
print(f'{app_path}: {module_id}')

# Define credential of the infrastructure service to start application on.
infra_cred_id = 'credential/78bdb494-4d8d-457a-a484-a582719ab32c'

# Define data.

# Data record ids.
data_records = ['data-record/36fe11cc-7f4f-4ee5-a123-0fafacf4a24b',
                'data-record/6803e2e4-1db6-42b4-8b8c-b3273c938366']
# Data object ids.
data_objects = ['data-object/36fe11cc-7f4f-4ee5-a123-0fafacf4a24b',
                'data-object/6803e2e4-1db6-42b4-8b8c-b3273c938366']
# Two ways to provide data sets: by referencing its id and by filter.
data_sets = [{'id': 'data-set/31d8ce24-7567-455e-9d39-4763c1d4010e',
              'time-start': '2020-01-14T23:00:00Z',
              'time-end': '2020-02-16T22:45:00Z'},
             {'filter': "content-type='gnss/perf-test' and gnss:station='nuvlabox-esac'",
              'data-type': 'data-object',
              'time-start': '2020-02-14T23:00:00Z',
              'time-end': '2020-03-16T22:45:00Z'}]

# Launch application referenced by `module_id` with data.
dpl = dpl_api.launch(module_id,
                     infra_cred_id=infra_cred_id,
                     data_sets=data_sets,
                     data_records=data_records,
                     data_objects=data_objects)
print(f'deployment:', dpl.id)
final = [Deployment.STATE_STARTED, Deployment.STATE_ERROR]
while dpl_api.state(dpl_api.get(dpl.id)) not in final:
    time.sleep(5)

# Terminate deployment.
res = dpl_api.terminate(dpl.id)

# Logout from Nuvla.
nuvla.logout()
