from ..extensions.base_resource import Resource
from ..control.COrder import COrder


class AOrder(Resource):
    def __init__(self):
        self.corder = COrder()

    def get(self, order):
        apis = {
            'list': self.corder.list,
            'get': self.corder.get
        }
        return apis

    def post(self, order):
        apis = {
            'create': self.corder.create,
            'wechat_notify': self.corder.wechat_notify,
            'test_over_ordermain': self.corder.test_over_ordermain,
            'send': self.corder.send,
        }
        return apis
