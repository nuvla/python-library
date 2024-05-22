#!/usr/bin/env python3

# import sys
# sys.path.insert(0,'/Users/jwhite/Code/python-library/nuvla/api/resources')
# from user import User
from nuvla.api import Api as Nuvla
from nuvla.api.resources.data import DataRecord
from nuvla.api.resources.user import User
from utils import nuvla_conf_user_pass

import random


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
session_string = user_api.login_password(username, password)
print('session_string:', session_string)
if 'active_claim' in user_api.get(session_string):
    print('Current group:', user_api.get(session_string)['active-claim'])
else:
    print('There is no active claim')

new_group = 'group/sixsq-devs'
print("\nSwitch to new group  ->  ", new_group)
user_api.switch_user_group(session_string, new_group)
print('Switched group to:', user_api.get(session_string)['active-claim'],'\n')

# Data record API object.
#
dr_api = DataRecord(nuvla)


#
# Add minimal data record.
#
# infrastructure-service is the only mandatory field at creation time.
dr_id = dr_api.create({}, 'infrastructure-service/1-2-3')
print('created simple data record:', dr_id)

assert dr_id == dr_api.delete(dr_id)
print('deleted simple data record:', dr_id)

#
# Add data record that describes an object on S3.
#
# s3_infra_service_id = 'infrastructure-service/771fa0f1-a38d-400b-bad4-3f7600f069af'
s3_infra_service_id = 'infrastructure-service/09b08b49-2408-4b80-a7cc-73f420903fd5'

# search for data records

## records = dr_api.id_by_name('African Lion', filter=f"infrastructure-service='{s3_infra_service_id}'")
records = dr_api.id_by_name('African Lion', filter=f"tags='lion'")

print(f'Found records\n', records)

for record in records:
    print(f'deleted data record:', dr_api.delete(record))

animals = ["lion", "elephant", "giraffe", "hyena", "rhino", "zebra"]

data_record = {
    "infrastructure-service": s3_infra_service_id,

    "description": "Scary lions in Africa",
    "name": "African Lion",

    "object": "african-lion.jpg",
    "bucket": "cloud.animals",
    "content-type": "animals/lion",

    "bytes": random.randint(1000, 100000),
    "platform": "S3",

    "another-field": "another-value",

    "yet-another-field": "yet-another-value",

    "tags": ["zoo", "africa", "lion", "not dog"]
}
dr_id = dr_api.add(data_record)
print('created data record:', dr_id)


#
# Delete data record.
#
# assert dr_id == dr_api.delete(dr_id)
# print('deleted data record:', dr_id)

# Logs out the user.
user_api.logout()
