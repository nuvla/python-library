#!/usr/bin/env python

import time
from nuvla.api import Api as Nuvla
from nuvla.api.resources.deployment import Deployment

# Login to Nuvla instance (running on localhost with self-signed cert).
nuvla = Nuvla(endpoint='https://localhost', insecure=True)
res = nuvla.login_password('super', 'supeR8-supeR8')
if not res.ok:
    raise Exception('Login failed: {}'.format(res.json().get('message', '')))

# Create Deployment API handler.
dpl_api = Deployment(nuvla)

# Define application module to start.
module_id = 'module/20b6ea7a-ee55-44e7-93e7-7f26b4caef18'

# Define credential of the infrastructure service to start application on.
infra_cred_id = 'credential/e2340ae1-56c1-405b-8b6f-340f279d0d66'

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
dpl_id = dpl_api.launch(module_id,
                        infra_cred_id=infra_cred_id,
                        data_sets=data_sets,
                        data_records=data_records,
                        data_objects=data_objects)

final = [Deployment.STATE_STARTED, Deployment.STATE_ERROR]
while dpl_api.state(dpl_api.get(dpl_id)) not in final:
    time.sleep(5)

# Terminate deployment.
res = dpl_api.terminate(dpl_id)

# Logout from Nuvla.
nuvla.logout()
