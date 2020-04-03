# -*- coding : utf-8 -*-
from ..control.CActivity import CActivity
from ..extensions.base_resource import Resource


class AActivity(Resource):
    def __init__(self):
        self.cactivity = CActivity()

    def get(self, activity):
        apis = {
            'list': self.cactivity.list_activity,
            'info': self.cactivity.info,
            'signed_up': self.cactivity.signed_up,
        }
        return apis

    def post(self, activity):
        apis = {
            'set': self.cactivity.set_activity,
            'sign_up': self.cactivity.sign_up,
        }

        return apis
