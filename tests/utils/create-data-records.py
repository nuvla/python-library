#!/usr/bin/env python

from datetime import datetime, timezone
import time
import sys

from nuvla.api import Api as Nuvla

debug = False
if debug:
    import requests
    import logging
    import http.client as http_client

    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

dr_object = {
    "description": "GNSS",
    "gnss:size": 49999800,
    "name": "GNSS",
    "gnss:lon": -1.1837999820709229,
    "infrastructure-service": "infrastructure-service/67df92a2-9553-46f3-88ee-0b1adfb53d7e",
    "gnss:bits": 8,
    "gnss:lat": 52.95220184326172,
    "gnss:unit_id": "00001",
    "gnss:hgt": 99,
    "gnss:timestamp": "20191003T144657Z",
    "host": "10.1.78.32:8080",
    "gnss:name": "perf-test-20191003T144657Z",
    "resource-type": "data-record",
    "content-type": "gnss/perf-test",
    "gnss:chain": 1,
    "bytes": 49999800,
    "timestamp": "2019-10-03T14:46:57Z",
    "gnss:type": "perf-test",
    "location": [
        52.95220184326172,
        -1.1837999820709229,
        99
    ],
    "object": "perf-test-20191003T144657Z",
    "bucket": "bucket-perf-test-20191003t140000z",
    "gnss:station": "nuvlabox-esac",
    "platform": "S3"
}


def create_data_key_prefix(nuvla):
    try:
        nuvla.add('data-record-key-prefix',
                  {"prefix": "gnss",
                   "uri": "http://sixsq.com/nuvla/schema/1/data/gnss"})
    except Exception as ex:
        if ex.response.status_code != 409:
            raise ex


def dr_create(nuvla: Nuvla, num_create: int):
    while num_create > 0:
        try:
            tm = datetime.utcnow().replace(tzinfo=timezone.utc) \
                .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            dr_object.update({'timestamp': tm})
            res = nuvla.add('data-record', dr_object)
            if res.data['status'] != 201:
                print('Failed to create object.')
            else:
                print('Created object.')
        except Exception as ex:
            print('Exception while adding data-record: {}'.format(ex))
        time.sleep(0.1)
        num_create -= 1


nuvla = Nuvla(endpoint='https://localhost', insecure=True)
res = nuvla.login_password('super', 'supeR8-supeR8')
if not res.ok:
    raise Exception('Login failed: {}'.format(res.json().get('message', '')))

if len(sys.argv) > 1:
    n = int(sys.argv[1])
else:
    n = 5

create_data_key_prefix(nuvla)
dr_create(nuvla, n)

nuvla.logout()
