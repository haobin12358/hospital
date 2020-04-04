# -*- coding : utf-8 -*-
from ..control.CUser import CUser
from ..extensions.base_resource import Resource


class AUser(Resource):
    def __init__(self):
        self.cuser = CUser()

    def get(self, user):
        apis = {
            'provinces': self.cuser.get_provinces,
            'cities': self.cuser.get_cities,
            'areas': self.cuser.get_areas,
            'address_list': self.cuser.address_list,
            'address': self.cuser.address,
            'info': self.cuser.info,
            'list_roles': self.cuser.list_roles,
            'list_family': self.cuser.list_family,
            'family': self.cuser.family,
            'list': self.cuser.list_user,
        }
        return apis

    def post(self, user):
        apis = {
            'mp_login': self.cuser.mini_program_login,
            'test_login': self.cuser.test_login,
            'set_address': self.cuser.set_address,
            'set_family': self.cuser.set_family,
            'identifying_code': self.cuser.send_identifying_code,
        }

        return apis
