#!/usr/bin/env python3

from pprint import pp
import time
import os
import re

from nuvla.api import Api as Nuvla
from nuvla.api.resources.module import Module, AppBuilderK8s, ProjectBuilder
from nuvla.api.resources.deployment import Deployment

email = "konstan+gssc2@sixsq.com"
passwd = "Saf8pass%"

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

#
# Login to Nuvla.
#
nuvla.login_password(email, passwd)

#
# Add data.
#

# Data record ids.
data_records = []

# Data object ids.
data_objects = []

# Two ways to provide data sets: by referencing its id and by filter.
data_sets = []
# data_sets = [{'id': 'data-set/31d8ce24-7567-455e-9d39-4763c1d4010e',
#               'time-start': '2020-01-14T23:00:00Z',
#               'time-end': '2020-02-16T22:45:00Z'},
#              {'filter': "content-type='gnss/perf-test' and gnss:station='nuvlabox-esac'",
#               'data-type': 'data-object',
#               'time-start': '2020-02-14T23:00:00Z',
#               'time-end': '2020-03-16T22:45:00Z'}]

#
# Module API handler.
#
module_api = Module(nuvla)

#
# Create project.
#
project_path = "data-processing"
project = ProjectBuilder() \
    .path(project_path) \
    .build()
project_id = module_api.add_module(project, exist_ok=True)
print("project id:", project_id)

#
# Create Application.
#

# TODO: create before
registry = 'infrastructure-service/aa5a18bb-d0e7-492a-bfd0-ca14d35c7056'

app_path = os.path.join(project_path, 'jupyter')
k8s_app = AppBuilderK8s() \
    .path(app_path) \
    .script(open('jupyter-k8s.yaml').read()) \
    .url('jupyter', 'https://${hostname}:${Service.jupyter.tcp.8888}/?token=${access-token}') \
    .output_parm('access-token') \
    .output_parm('public-port') \
    .data_content_type('application/jupyter') \
    .registry(registry) \
    .build()
k8s_app_id = module_api.add_module(k8s_app, exist_ok=True)
print('k8s app id:', k8s_app_id)

#
# Launch deployment.
#

# Create Deployment API handler.
dpl_api = Deployment(nuvla)

# TODO: Define credential of the infrastructure service to start application on.
infra_cred_id = 'credential/e2340ae1-56c1-405b-8b6f-340f279d0d66'

# Launch application referenced by `module_id` with data.
dpl = dpl_api.launch(k8s_app_id, infra_cred_id=infra_cred_id,
                     data_sets=data_sets, data_objects=data_objects,
                     data_records=data_records)

while True:
    print('Waiting for deployment to enter started state.')
    time.sleep(5)
    dpl = dpl_api.get(dpl.id)
    if dpl_api.state(dpl) == Deployment.STATE_ERROR:
        print('Deployment failed.')
        exit(1)
    elif dpl_api.state(dpl) == Deployment.STATE_STARTED:
        break
print('Deployment started.')

#
# Get deployment logs.
#
app_service = 'jupyter'
check_msg = 'The Jupyter Notebook is running'

wait_time = 10*60
time_stop = time.time() + wait_time
logs = dpl_api.init_logs(dpl, app_service)
while True:
    logs = dpl_api.get_logs(logs)
    found = False
    for line in dpl_api.logs(logs):
        if re.search(check_msg, line):
            print('Found in logs:', line)
            found = True
    if found:
        break
    if time.time() >= time_stop:
        print('Service {0} is not running after {1} seconds.'
              .format(app_service, wait_time))
        exit(1)
    print('Waiting 5 sec for logs...')
    time.sleep(5)

print('Service {} deployed successfully!'.format(app_service))

#
# Terminate deployment.
#
print('Terminating deployment ...')
resp = dpl_api.terminate(dpl.id, timeout=60)
print('Deployment terminated.')

#
# Logout.
#
nuvla.logout()

