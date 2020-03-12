# -*- coding : utf-8 -*-
from hospital.extensions.base_resource import Resource
from hospital.control.CConfig import CConfig

class AConfig(Resource):
    def __init__(self):
        self.cconfig = CConfig()

    def get(self, config):
        apis = {
            "list_banner": self.cconfig.list_banner,
            "get_csd": self.cconfig.get_csd,
            "get_about_us": self.cconfig.get_about_us
        }

        return apis

    def post(self, config):
        apis = {
            "set_banner": self.cconfig.set_banner,
            "set_csd": self.cconfig.set_csd,
            "set_about_us": self.cconfig.set_about_us
        }

        return apis