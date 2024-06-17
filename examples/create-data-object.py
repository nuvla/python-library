#!/usr/bin/env python3

import os
import hashlib
from pprint import pp

from nuvla.api import Api as Nuvla
from nuvla.api.resources.data import DataObjectS3
from nuvla.api.resources.data import DataRecord
from nuvla.api.resources.user import User
from nuvla.api.api import NuvlaError
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
# user_api.login_password(username, password)
user_api.login(username, password)

# REQUIRED: ID of S3 credential in Nuvla.
# either we already know this and it is hardcoded below
# s3_cred_id = 'credential/362e6088-394d-4de9-9667-8e1a40136aa6'
# s3_cred_id = 'credential/0f70f0fb-c226-4fc2-a98b-61f0646813d7'

# OR we can get the credentials from a login if we want...
# as in below
creds = nuvla.get('credential')
s3_cred_id = None
for cred in creds.data['resources']:
    try:
        parent = nuvla.get(cred['parent'])
        if "s3" in str(parent.data['subtype']) and "Exoscale" in str(parent.data['name']):
            s3_cred_id = str(cred['id'])
            print(f"Found Exoscale S3 credential: {s3_cred_id}")
    except (NuvlaError, KeyError):
        pass
# if we didn't find the credential, we should exit
if not s3_cred_id:
    print("No Exoscale S3 credential found. Exiting.")
    exit(1)

#
# Set correct values for variable below.
#
# Bucket to store the test objects.
# bucket will be created if it doesn't exist?
#
bucket = 'bucket-for-extract-project-demo-purposes-002'
# can we get the bucket name from the credential?

#
# data-object API object.
#
data_obj_api = DataObjectS3(nuvla)

def generate_event(local_event_record: dict) -> str:
    '''
    Generate an event in Nuvla
    :param local_event_record: dict - event record
    :return: str - event id
    '''
    try:
        cimi_event = nuvla.add('event', local_event_record)
    except NuvlaError as e:
        print(f'Failed to create event: {e}')
        return None
    event_id = cimi_event.data['resource-id']
    print('created event:', event_id, "with data:")
    pp(cimi_event.data)
    return event_id

# should generate an event here as a data record was create
# maybe this should be combined?

def create_data_record(local_data_record: dict) -> str:
    '''
    Create a data record in Nuvla
    :param local_data_record: dict - data record
    :return: str - data record id
    if the data record already exists, it will be deleted and recreated
    possibly should be a recursive function
    '''
    try:
        dr_id_created = dr_api.add(local_data_record)
    except NuvlaError as e:
        print(f'Failed to create data record: {e}')
        for arg in e.args:
            if 'data-record' in arg:
                dr_id_created = arg.split(' ')[-1]
                print(f'Data record already exists, data record id: {dr_id_created}. Deleting and recreating.')
                deleted_dr_id = dr_api.delete(dr_id_created)
                if deleted_dr_id:
                    print('Deleted data record id:', deleted_dr_id)
                    dr_id_created = create_data_record(local_data_record)
                    break
        
        return dr_id_created

    return dr_id_created

def create_data_object(local_content, local_bucket: str, local_object_path: str, local_s3_cred_id: str, local_content_type: str, local_tags) -> str:
    try:
        object_id = data_obj_api.create(local_content, local_bucket, 
                                        local_object_path, local_s3_cred_id,
                                        content_type=local_content_type,
                                        tags=local_tags)
    except NuvlaError as e:
        print(f'Failed to create data object: {e}') 
        for arg in e.args:
            if 'data-object' in arg:
                object_id = arg.split(' ')[-1]
                print(f'\n\nObject already exists, object id: {object_id}. Deleting and recreating.')
                deleted_object_id = data_obj_api.delete(object_id)
                if deleted_object_id:
                    print(f'Deleted object id: {deleted_object_id}')
                    object_id = create_data_object(local_content, local_bucket, local_object_path, local_s3_cred_id, local_content_type, local_tags)
                    print(f'Created object id: {object_id}\n\n')
                    break
        return object_id
    return object_id

#
# Create binary object on S3 and register it in Nuvla.
#
print("\nCreating binary object\n")
# here is the file that actually gets uploaded to S3
content = open('data/african-lion.jpg', 'rb').read()
# here is the path where the file will be stored in S3
object_path = 'africa/african-lion3.jpg'
# here is the content type of the file
content_type = 'image/scary-lions'


# Add binary object.
# Bucket will be created if it doesn't exist.
# tags can be added to the object
tags = ["zoo", "africa", "lion"]
bin_object_id = create_data_object(content, bucket, \
                              object_path, s3_cred_id, \
                              content_type, tags)
# Get object document.
# print out the object document
obj_doc = data_obj_api.get(bin_object_id)
pp(obj_doc)

# create a data record for the object
dr_api = DataRecord(nuvla)
# find the S3 infrastructure service
# either it's known and hardcoded or we can search for it using the credential
# s3_infra_service_id = 'infrastructure-service/09b08b49-2408-4b80-a7cc-73f420903fd5'
cred_doc = nuvla.get(s3_cred_id) 
s3_infra_service_id=cred_doc.data['parent']
if not s3_infra_service_id:
    print('No infrastructure service found for the credential. Exiting.')
    exit(1)

data_record = {
    "infrastructure-service": s3_infra_service_id,

    "description": "Lions in Africa",
    "name": "African Lion",
    "object": object_path,
    "bucket": bucket,
    "content-type": "animals/lion",
    "bytes": len(content),
    "platform": "S3",
    "tags": ["zoo", "africa", "lion", "whatevs"],
    "another-field": "another-value",
    "yet-another-field": "yet-another-value",
    "and-another-field": "and-another-value",   
}

# dr_id = dr_api.add(data_record)
print('\n\ncreating data record\n\n')
dr_id = create_data_record(data_record)
print('created data record:', dr_id)
pp(dr_api.get(dr_id))

event_record = {
    "category": "user",
    "content": {
      "resource": {
        "href": dr_id, # this must be the data record id
        "content": {
          "content-type": content_type,
        },
      },
      "state": "created",
    },
    "severity": "medium",
    "tags": data_record['tags'],
}

event = generate_event(event_record)
event_structure = nuvla.get(event).data
pp(event_structure)

# Download object and store it locally to a file.
local_filename = './data/local-african-lion.jpg'
data_obj_api.get_to_file(bin_object_id, local_filename)
# Verify checksum.
assert hashlib.md5(content).hexdigest() \
       == hashlib.md5(open(local_filename, 'rb').read()).hexdigest()
os.unlink(local_filename)

# get a list of data records
records = dr_api.id_by_name('African Lion', filter=f"tags='lion'")
# pp(records)
for record in records:
    # pp(dr_api.get(record))
    try:
        dr_api.get(record)['content']['resource']['href']
        print(f'New style data {record} record, probably should NOT delete it.')
    except KeyError:
        # print(f'Old style data {record} record, could delete it.') 
        print(f'Deleted old style data record:', dr_api.delete(record))      
# exit(1)

# Create a text object on S3 and register it in Nuvla.
#
content = open('./data/african-lion.txt', 'r').read()

object_path = 'africa/african-lion-zebra.txt'
content_type = 'plain/text'

# Add text object.
# Bucket will be created if doesn't exist.

print("\nCreating text object\n")
str_object_id = create_data_object(content, bucket, \
                              object_path, s3_cred_id, \
                              content_type, tags)

# Get object document.
obj_doc = data_obj_api.get(str_object_id)
pp(obj_doc)

# Download object and store it locally to a file.
local_filename = './data/local-african-lion.txt'
data_obj_api.get_to_file(str_object_id, local_filename)
# Verify checksum.
assert hashlib.md5(content.encode()).hexdigest() \
       == hashlib.md5(open(local_filename, 'r').read().encode()).hexdigest()
os.unlink(local_filename)

# here we could do the same data_record and event creation as above
# but we won't for now

#
# Delete object from Nuvla and S3. Bucket gets deleted as well if it's empty.
# these are commented out to avoid deleting the objects.
#
# assert bin_object_id == data_obj_api.delete(bin_object_id)
# assert str_object_id == data_obj_api.delete(str_object_id)

# Logs out the user.
user_api.logout()
