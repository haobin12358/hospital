
from ..extensions.base_resource import Resource
from ..control.CRegister import CRegister


class ARegister(Resource):
    def __init__(self):
        self.cregister = CRegister()

    def get(self, register):
        apis = {
            'list': self.cregister.list
        }
        return apis

    def post(self, register):
        apis = {
            'add': self.cregister.add_register
        }
        return apis
