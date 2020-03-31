#!/usr/bin/env python3

from pprint import pp
import os
from nuvla.api import Api as Nuvla, NuvlaError
from nuvla.api.resources.module import Module, AppBuilderK8s, ProjectBuilder

email = "konstan+gssc2@sixsq.com"
passwd = "Saf8pass%"

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

# Login to Nuvla.
nuvla.login_password(email, passwd)

# Module API handler.
module_api = Module(nuvla)

# Create project.
project_path = "data-processing"
project = ProjectBuilder() \
    .path(project_path) \
    .build()
project_id = module_api.add_module(project, exist_ok=True)
print("project id:", project_id)

# Create Application.
app_path = os.path.join(project_path, 'jupyter')
k8s_app = AppBuilderK8s() \
    .path(app_path) \
    .script(open('jupyter-k8s.yaml').read()) \
    .url('jupyter', 'https://${hostname}:${Service.jupyter.tcp.8888}/?token=${access-token}') \
    .output_parm('access-token') \
    .output_parm('public-port') \
    .data_content_type('application/jupyter') \
    .registry('infrastructure-service/aa5a18bb-d0e7-492a-bfd0-ca14d35c7056') \
    .build()
k8s_app_id = module_api.add_module(k8s_app, exist_ok=True)
print('k8s app id:', k8s_app_id)

# Get Application by path.
app = module_api.get_by_path(app_path)
assert app['path'] == app_path

# Update name and description.
app_updated = AppBuilderK8s(app) \
    .name('Jupyter Lab') \
    .description('For jovyans.') \
    .commit('updated name and description') \
    .build()
app = module_api.update(app_updated)
assert app['name'] == 'Jupyter Lab'

nuvla.logout()

