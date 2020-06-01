import os
import requests
from typing import Optional, Union

from nuvla.api import Api as Nuvla
from .base import ResourceBase


class DataRecord(ResourceBase):
    resource = 'data-record'

    def create(self, data: dict, infra_service_id: str):
        if isinstance(data, dict):
            data.update({'infrastructure-service': infra_service_id})
            return self.add(data)


class DataObjectS3(ResourceBase):
    resource = 'data-object'

    def __init__(self, nuvla: Nuvla):
        super().__init__(nuvla)

    def create(self, content: Union[str, bytes], bucket, object_path, s3_cred_id,
               content_type='text/plain', name=None, description=None,
               tags: Optional[list]=None, md5sum: Optional[str]=None) -> str:
        """Stores `content` in S3 defined by `s3_cred_id` and registers the
        object as data-object in Nuvla. Returns data-object resource ID.
        `content` and `content_type` should match (e.g. str and plain/text,
        bytes and image/png).
        """
        doc = {
            "template": {
                "name": name or object_path,
                "description": description or name or object_path,
                "credential": s3_cred_id,
                "subtype": "generic",
                "resource-type": "data-object-template",
                "content-type": content_type,
                "object": object_path,
                "bucket": bucket,
                "bytes": len(content),
                "href": "data-object-template/generic"
            }
        }
        if tags:
            doc["template"].update({'tags': tags})
        if md5sum:
            doc["template"].update({'md5sum': md5sum})

        data_object_id = self.add(doc)

        # Upload data.
        data_object = self.nuvla.get(data_object_id)
        response = self.nuvla.operation(data_object, "upload")
        upload_url = response.data['uri']
        headers = {"content-type": content_type}
        response = requests.put(upload_url, data=content, headers=headers)
        response.raise_for_status()

        # Set object is ready.
        data_object = self.nuvla.get(data_object_id)
        self.nuvla.operation(data_object, "ready")

        return data_object_id

    def get_content(self, object_id) -> Union[str, bytes]:
        """Returns string or bytes array by downloading from S3 the object
        identified by `object_id`. They type of the returned object
        corresponds to the `content-type` of the object (text or binary).
        """
        data_object = self.nuvla.get(object_id)
        response = self.nuvla.operation(data_object, 'download')
        download_url = response.data['uri']
        content_type = data_object.data['content-type']

        headers = {'content-type': content_type}
        response = requests.get(download_url, headers=headers)
        return response.content

    def get_to_file(self, object_id, filename=''):
        """Downloads from S3 and stores to a file the content of the S3 object
        identified by `object_id`. If `filename` is not given, the base name
        of 'object' attribute is taken instead.
        """
        content = self.get_content(object_id)
        if not filename:
            data_object = self.nuvla.get(object_id)
            filename = os.path.basename(data_object.data['object'])
        if isinstance(content, bytes):
            fmode = 'wb'
        else:
            fmode = 'w'
        with open(filename, fmode) as fh:
            fh.write(content)

    def delete(self, resource_id) -> str:
        """Deletes object from S3 and its record from Nuvla identified by
        `resource_id`. Returns ID of the deleted object.
        """
        return super().delete(resource_id)


class DataSet:
    pass
