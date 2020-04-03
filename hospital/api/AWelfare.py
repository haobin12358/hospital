# -*- coding : utf-8 -*-
from ..control.CWelfare import CWelfare
from ..extensions.base_resource import Resource


class AWelfare(Resource):
    def __init__(self):
        self.cwelfare = CWelfare()

    def get(self, welfare):
        apis = {
            'list': self.cwelfare.list,
            'get': self.cwelfare.get,
            'userlist': self.cwelfare.userlist
        }
        return apis

    def post(self, welfare):
        apis = {
            'set_coupon': self.cwelfare.set_coupon
        }

        return apis