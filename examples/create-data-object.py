#!/usr/bin/env python3

import os
import hashlib
from pprint import pp

from nuvla.api import Api as Nuvla
from nuvla.api.resources.data import DataObjectS3
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

#
# Set correct values for variable below.
#

# REQUIRED: ID of S3 credential in Nuvla.
# s3_cred_id = 'credential/362e6088-394d-4de9-9667-8e1a40136aa6'
s3_cred_id = 'credential/0f70f0fb-c226-4fc2-a98b-61f0646813d7'

# Bucket to store the test objects.
bucket = 'bucket-for-extract-project-demo-purposes-001'

#
# data-object API object.
#
data_obj_api = DataObjectS3(nuvla)

#
# Create binary object on S3 and register it in Nuvla.
#
content = open('data/african-lion.jpg', 'rb').read()

object_path = 'africa/african-lion2.jpg'
content_type = 'image/jpg'

def create_object(content, bucket: str, object_path: str, s3_cred_id: str, content_type: str, tags) -> str:
    try:
        bin_object_id = data_obj_api.create(content, bucket, object_path, s3_cred_id,
                                            content_type=content_type,
                                            tags=tags)
    except NuvlaError as e:
        for arg in e.args:
            if 'data-object' in arg:
                bin_object_id = arg.split(' ')[-1]
                print('Object already exists, object id:', bin_object_id)
                deleted_object_id = data_obj_api.delete(bin_object_id)
                print('Deleted object id:', deleted_object_id)
                bin_object_id = create_object(content, bucket, object_path, s3_cred_id, content_type, tags)
                break   
        
        return bin_object_id

    print('.png object id:', bin_object_id)
    return bin_object_id

# Add binary object.
# Bucket will be created if it doesn't exist.
bin_object_id = create_object(content=content, bucket=bucket, \
                              object_path=object_path, s3_cred_id=s3_cred_id, \
                              content_type=content_type, tags=["zoo", "africa", "lion"])

print(f'.png object id: {bin_object_id}')


# Get object document.
obj_doc = data_obj_api.get(bin_object_id)
pp(obj_doc)

# Download object and store it locally to a file.
local_fn = './data/local-african-lion.jpg'
data_obj_api.get_to_file(bin_object_id, local_fn)
# Verify checksum.
assert hashlib.md5(content).hexdigest() \
       == hashlib.md5(open(local_fn, 'rb').read()).hexdigest()
os.unlink(local_fn)

#
# Create a text object on S3 and register it in Nuvla.
#
content = open('./data/african-lion.txt', 'r').read()

object_path = 'africa/african-lion-zebra.txt'
content_type = 'plain/text'

# Add text object.
# Bucket will be created if doesn't exist.

str_object_id = create_object(content, bucket, object_path, s3_cred_id, content_type, tags=["zoo", "africa", "lion"])

print('.txt object id:', str_object_id)

# Get object document.
obj_doc = data_obj_api.get(str_object_id)
pp(obj_doc)

# Download object and store it locally to a file.
local_fn = './data/local-african-lion.txt'
data_obj_api.get_to_file(str_object_id, local_fn)
# Verify checksum.
assert hashlib.md5(content.encode()).hexdigest() \
       == hashlib.md5(open(local_fn, 'r').read().encode()).hexdigest()
os.unlink(local_fn)


#
# Delete object from Nuvla and S3. Bucket gets deleted as well if it's empty.
# these are commented out to avoid deleting the objects.
#
# assert bin_object_id == data_obj_api.delete(bin_object_id)
# assert str_object_id == data_obj_api.delete(str_object_id)

# Logs out the user.
user_api.logout()
