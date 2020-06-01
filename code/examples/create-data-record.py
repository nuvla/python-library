#!/usr/bin/env python3

from nuvla.api import Api as Nuvla
from nuvla.api.resources.data import DataRecord
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
# Data record API object.
#
dr_api = DataRecord(nuvla)


#
# Add minimal data record.
#
# infrastructure-service is the only mandatory field at creation time.
dr_id = dr_api.create({}, 'infrastructure-service/1-2-3')
print('created data record:', dr_id)

assert dr_id == dr_api.delete(dr_id)
print('deleted data record:', dr_id)

#
# Add data record that describes an object on S3.
#
s3_infra_service_id = 'infrastructure-service/771fa0f1-a38d-400b-bad4-3f7600f069af'
data_record = {
    "infrastructure-service": s3_infra_service_id,

    "description": "Lions in Africa",
    "name": "African Lion",

    "object": "african-lion.jpg",
    "bucket": "cloud.animals",
    "content-type": "animals/lion",

    "bytes": 12499950,
    "platform": "S3",

    "tags": ["zoo", "africa", "lion"]
}
dr_id = dr_api.add(data_record)
print('created data record:', dr_id)


#
# Delete data record.
#
assert dr_id == dr_api.delete(dr_id)
print('deleted data record:', dr_id)

# Logs out the user.
user_api.logout()
