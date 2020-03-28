import oss2

from hospital.config.secret import ACCESS_KEY_ID, ACCESS_KEY_SECRET, ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT


class AliyunOss(object):
    """
    官方SDK文档 https://help.aliyun.com/document_detail/32027.html?spm=a2c4g.11186623.6.840.36845fffiMqKKk
    """

    def __init__(self, app=None):
        self.app = app
        if app is None:
            raise Exception('app丢失')
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

    def save(self, data, filename=None):
        if filename is not None:  # 文件大小不能超过5G
            self.bucket.put_object_from_file(filename, data)

    def delete(self, filename=None):
        if filename is not None:
            self.bucket.delete_object(filename)
