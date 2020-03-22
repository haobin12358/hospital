from ..control.CExample import CExample
from ..extensions.base_resource import Resource


class AExample(Resource):

    def __init__(self):
        self.cexample = CExample()

    def get(self, example):
        apis = {
            'get': self.cexample.get,
            'list': self.cexample.list,
        }
        return apis

    def post(self, example):
        apis = {
            'add_or_update_example': self.cexample.add_or_update_example
        }
        return apis
