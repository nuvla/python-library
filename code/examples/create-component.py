#!/usr/bin/env python3

import os
from nuvla.api import Api as Nuvla, NuvlaError
from nuvla.api.resources.module import Module, AppBuilderK8s, ProjectBuilder

email = "konstan+gssc2@sixsq.com"
passwd = "Saf8pass%"

# Create Nuvla client. No authentication required.
nuvla = Nuvla()
# nuvla = Nuvla(endpoint='https://nuvla.io', insecure=True)

nuvla.login_password(email, passwd)

module_api = Module(nuvla)

project_path = "data-processing"

project = ProjectBuilder().path(project_path).build()
project_id = module_api.add_module(project)
print("project id:", project_id)

k8s_app = AppBuilderK8s() \
    .path(project_path + '/' + 'jupyter') \
    .script(open('jupyter.yaml').read()) \
    .build()
k8s_app_id = module_api.add_module(k8s_app)
print('k8s app id:', k8s_app_id)
exit()


module_response = nuvla.add('module', module)
module_id = module_response.data['resource-id']
print("module id: %s\n" % module_id)
