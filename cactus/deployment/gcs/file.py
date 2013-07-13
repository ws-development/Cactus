#coding:utf-8
import io
import base64

from apiclient.http import MediaIoBaseUpload
from cactus.deployment.file import BaseFile


class GCSFile(BaseFile):
    def get_metadata(self):
        """
        Generate metadata for the upload.
        Note: we don't set the etag, since the GCS API does not accept what we set
        """
        metadata = {
            "acl": {"entity": "allUsers", "role": "READER",},
            "md5Hash": base64.b64encode(self.payload_checksum.decode('hex')),
            "contentType": self.content_type,  # Given twice...
            "cacheControl": unicode(self.cache_control)  # That's what GCS will return
        }

        if self.content_encoding is not None:
            metadata['contentEncoding'] = self.content_encoding

        return metadata

    def remote_changed(self):
        """
        Compare each piece of metadata that we're setting with the one that's stored remotely
        If one's different, upload again.

        :rtype: bool
        """
        resource = self.engine.service.objects()
        req = resource.get(bucket=self.engine.bucket_name, object=self.path)
        remote_metadata = req.execute()

        ignore_metadata = ["acl"] # We can't control what we'll retrieve TODO: do the best we can do!

        for k, v in self.get_metadata().items():
            if k not in ignore_metadata and remote_metadata.get(k) != v:
                return True
        return False

    def do_upload(self):
        resource = self.engine.service.objects()

        stream = io.BytesIO(self.payload())
        upload = MediaIoBaseUpload(stream, mimetype=self.content_type)

        req = resource.insert(
            bucket=self.engine.bucket_name,
            name=self.path,
            body=self.get_metadata(),
            media_body=upload,
        )

        req.execute()
