"""
Producer takes an object and puts it into the Nuvla data catalogue. It will also trigger the necessary events to notify
"""
from datetime import datetime, timezone
from pprint import pprint
from typing import Union, Optional

from nuvla.api.resources.data import DataObjectS3, DataRecord
from nuvla.api import Api as Nuvla


class DataProducer:
    def __init__(self, nuvla: Nuvla, bucket: str, s3_credential: str, infra_service_id: str):
        # Nuvla client should be logged in at this stage
        self.nuvla: Nuvla = nuvla
        self.data_client: DataObjectS3 = DataObjectS3(nuvla)
        self.record_client: DataRecord = DataRecord(nuvla)

        self.bucket: str = bucket
        self.s3_credential: str = s3_credential
        self.infra_service_id: str = infra_service_id

    def produce(self, content: Union[str, bytes, None], object_path,
                content_type='text/plain', name=None, description=None,
                tags: Optional[list] = None, md5sum: Optional[str] = None):
        """
        Produce a new object in the data catalogue
        """
        # Create new Data object
        object_id: str = self.data_client.create(content, self.bucket, object_path, self.s3_credential,
                                                 content_type, name, description, tags, md5sum)
        pprint(f"Created data object: {object_id}")

        ts: str = datetime.utcnow().replace(tzinfo=timezone.utc) \
            .replace(microsecond=0).isoformat().replace('+00:00', 'Z')

        # Create new Data record
        record_id: str = self.create_data_record(object_id, name, description, content_type, ts, tags)
        pprint(f"Created data record: {record_id}")

        event_id: str = self.create_event(record_id, content_type, tags)
        pprint(f"Created event: {event_id}")

    def create_event(self, record_id: str, content_type: str, tags: Optional[list] = None):
        """
        Create a new event in the data catalogue
        """
        ts = datetime.utcnow().replace(tzinfo=timezone.utc) \
            .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        event_data = {
            "category": "user",
            "name": "Data-Record-Event",
            "description": "Event for {}".format(record_id),
            "content": {
                "resource": {
                    "href": record_id,  # this must be the data record id
                    "content": {
                        "content-type": content_type,
                    },
                },
                "state": "created",
            },
            "severity": "medium",
            "timestamp": ts
        }
        if tags:
            event_data.update({'tags': tags})
        event = self.nuvla.add('event', event_data)
        return event.data['resource-id']

    def create_data_record(self, object_id: str, name: str, description: str, content_type: str, ts: str,
                           tags: Optional[list] = None):
        """
        Create a new data record in the data catalogue
        """

        record_data = {
            "name": name,
            "data-object": object_id,
            "content-type": content_type,
            "timestamp": ts,
            "resource:object": object_id,
            "infrastructure-service": self.infra_service_id
        }
        if description:
            record_data.update({'description': description})
        if tags:
            record_data.update({'tags': tags})
        record_id = self.record_client.create(record_data, self.infra_service_id)
        return record_id


def new_s3_object(s3_cred_id: str):
    """
    New S3 object receives the information of a new object in the S3 bucket.
    The object has to be updated before calling this function by the user.
    """
