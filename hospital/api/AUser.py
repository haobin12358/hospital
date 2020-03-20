# -*- coding : utf-8 -*-
from ..control.CUser import CUser
from ..extensions.base_resource import Resource


class AUser(Resource):
    def __init__(self):
        self.cuser = CUser()

    def post(self, user):
        apis = {
            'mp_login': self.cuser.mini_program_login,
        }

        return apis
