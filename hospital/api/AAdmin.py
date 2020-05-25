# -*- coding : utf-8 -*-
from hospital.extensions.base_resource import Resource
from hospital.control.CAdmin import CAdmin

class AAdmin(Resource):
    def __init__(self):
        self.cadmin = CAdmin()

    def get(self, admin):
        apis = {
            "get_admin_list": self.cadmin.get_admin_list
        }

        return apis

    def post(self, admin):
        apis = {
            "add_admin": self.cadmin.add_admin,
            "admin_login": self.cadmin.admin_login,
            "update_admin_password": self.cadmin.update_admin_password,
            "delete_admin": self.cadmin.delete_admin,
            "reset_password": self.cadmin.reset_password,
            "refresh_token": self.cadmin.refresh_token,
        }

        return apis