from ..control.CExample import CExample
from ..extensions.base_resource import Resource


class AEXample(Resource):

    def __init__(self):
        self.cexample = CExample()

    def get(self, doctor):
        apis = {
            'get': self.cexample.get,
            'list': self.cexample.list,
        }
        return apis

    def post(self, doctor):
        apis = {
            'add_or_update_doctor': self.cexample.add_or_update_example
        }
        return apis
