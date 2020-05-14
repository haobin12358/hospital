
from ..extensions.base_resource import Resource
from ..control.CRegister import CRegister


class ARegister(Resource):
    def __init__(self):
        self.cregister = CRegister()

    def get(self, register):
        apis = {
            'list': self.cregister.list,
            'list_calling': self.cregister.list_calling
        }
        return apis

    def post(self, register):
        apis = {
            'add': self.cregister.add_register,
            'set_register': self.cregister.set_register,
        }
        return apis
