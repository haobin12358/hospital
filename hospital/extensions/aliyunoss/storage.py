import oss2


class AliyunOss(object):
    """
    官方SDK文档 https://help.aliyun.com/document_detail/32027.html?spm=a2c4g.11186623.6.840.36845fffiMqKKk
    """

    def __init__(self, access_key_id, access_key_secret, ali_oss_bucket_name, ali_oss_endpoint):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.ali_oss_bucket_name = ali_oss_bucket_name
        self.ali_oss_endpoint = ali_oss_endpoint

    @property
    def auth(self):
        return oss2.Auth(self.access_key_id, self.access_key_secret)

    @property
    def bucket(self):
        return oss2.Bucket(self.auth, self.ali_oss_endpoint, self.ali_oss_bucket_name)

    def save(self, data, filename=None):
        if filename is not None:  # 文件大小不能超过5G
            self.bucket.put_object_from_file(filename, data)

    def delete(self, filename=None):
        if filename is not None:
            self.bucket.delete_object(filename)
