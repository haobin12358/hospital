# -*- coding: utf-8 -*-
from ..control.CFile import CFile
from hospital.extensions.base_resource import Resource


class AFile(Resource):
    def __init__(self):
        self.cfile = CFile()

    def post(self, file):
        apis = {
            'upload': self.cfile.upload_img,
            'remove': self.cfile.remove,
            'batch_upload': self.cfile.batch_upload
        }
        return apis
