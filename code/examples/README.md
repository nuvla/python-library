# Examples of usage of nuvla-api library

The Python scripts in this directory use `nuvla-api`. To install the library run:

```
pip3 install nuvla-api
```

The code in the scripts is well commented. Please refer to the scripts for
details.

# Prerequisites

To start using the library, please import `nuvla.api.Api` module. This module
acts as a lower level API client to Nuvla. The default endpoint is
`https://nuvla.io`:

```
from nuvla.api import Api as Nuvla

# Create Nuvla client. By default `https://nuvla.io` endpoint is used.
nuvla = Nuvla()
```

In case of using different Nuvla instance provide `endpoint=https://<host|IP>`,
and if self-signed TLS certificate is used, provide `insecure=True`.

```
from nuvla.api import Api as Nuvla

nuvla = Nuvla(endpoint='https://nuvla.local', insecure=True)
```

# Create User

[user-create.py](user-create.py)

User creation doesn't require login to Nuvla. The script can be run as follows:

```
$ ./user-create.py
New user created: user/b8762055-4dec-4724-a65d-65b006d694ae
Validation email was sent to konstan+gssc2@sixsq.com.
$
```

To confirm the sign up to the service, use now has to validate it by clicking on 
the validation link in the email. Note: Nuvla instance must have been configured
with SMPT server.

# User login and logout

[user-loginout.py](user-loginout.py) shows how login and logout a user. As a
result of login operation a session is returned.

```
$ ./user-loginout.py
session/228cb944-821f-4123-8100-bfcedd6d7200
$
```

# Create Infrastructure Service Group

Before starting provisioning containers using Nuvla, endpoints and credentials
of Container Orchestration Engines (Docker Swarm and Kubernetes) must be added
to Nuvla as infrastructure services (IS). To facilitate the management of the
infrastructure services they can be grouped into infrastructure service groups.
In the case of the grouping, the group becomes parent of infrastructure
services.

Nuvla allows defining private Docker Registries with their corresponding
credentials to facilitate deployment of containers from the images coming from 
private registries. It's a good practice to define infrastructure service group
for the registry as well.

[create-infra-service-group.py](create-infra-service-group.py) shows how to
create infrastructure service group.

```
$ ./create-infra-service-group.py
infra service group: infrastructure-service-group/19ce4191-da42-4831-9903-ef056b7d4d4f
infra service registry group: infrastructure-service-group/3a88ced8-0ab2-46d4-bfe1-95c235e77af6
$
```

# Create Infrastructure Service

Different types of infrastructure services can be added to Nuvla: Docker
Swarm, Kubernetes, S3, Docker Registry.

Infrastructure services set infrastructure service group ID as their parent to
indicate they are part of the same group. Knowing infrastructure service group
ID one can discover services that belong to the same "site" and hence, are
logically grouped. This promotes discovery. For example, if one knows
infrastructure service ID of data endpoint - S3, it's possible to discover the
corresponding Kubernetes or Docker swarm ones, and visa versa. This mechanism
for example can be used in scheduling of data processing related tasks.

[create-infra-service.py](create-infra-service.py) shows how infrastructure
services can be created and added to a group (only one group is possible).
Please take the IDs of the groups created in the previous step and change group
IDs defined in the script.

```
$ ./create-infra-service.py
Kubernetes: infrastructure-service/13b419c0-c50a-4f97-826f-8eae16f68f64
S3: infrastructure-service/6d0b48c4-2608-46f4-9734-6a7e5a2135d8
Docker registry: infrastructure-service/19e1c37b-8bdc-43b8-8dab-eb378ac61e1f
$
```

# Create Infrastructure Service Credential

To access any of the infrastructure services users need credentials.

[create-infra-service-cred.py](create-infra-service-cred.py) shows how to create
such credentials on the example of Kubernetes and S3 infrastructure services. To
express the relationship, credential defines an IS as its parent (only one
parent is possible).

```
$ ./create-infra-service-cred.py
Kubernetes: credential/e2340ae1-56c1-405b-8b6f-340f279d0d66
S3: credential/b0b5734e-0eb8-4f02-8aac-c14d7c9379a6
$
```

# Create Application

Internally Nuvla uses concept of a module, and structures user defined projects
and applications using the modules. There are following module types: project,
component, application. 

[create-app.py](create-app.py) first creates a module of type project and then
creates an application of subtype kubernetes inside of the project.

```
$ ./create-app.py
module/92614bdc-4afa-49e1-891f-0eb3a4db0635
```

# Create data records

Data records is on of the two data types in Nuvla. It is designed to hold
location of the data and its description - meta-data. It's a document with a
number of requered root level fields with all the rest being free schema for the
user to define prefixed with <user prefix>:.

```
$ ./create-data-record.py
data-record/93344bdc-4afa-49e1-891f-0eb3a4db0886
```

# Create data object

```
$ ./create-data-object.py
data-object/72614bdc-4afa-49e1-891f-0eb3a4db0634
```

# Search for data records/objects

```
$ ./search-data.py
data-record/93344bdc-4afa-49e1-891f-0eb3a4db0886
```

# Bulk delete data records/objects

```
$ ./bulk-delete-data.py
deleted: data-record/93344bdc-4afa-49e1-891f-0eb3a4db0886
deleted: data-record/93344bdc-4afa-49e1-891f-0eb3a4db0886
```

# Create data set

```
$ ./create-data-set.py
data-set/98744bdc-4afa-49e1-891f-0eb3a4db0ea7
```

# Deploy Application

```
$ ./deploy-app.py
deployment/ec344bdc-4afa-49e1-891f-0eb3a4db0971
```

# Get Application logs

```
$ ./app-logs.py
...
```