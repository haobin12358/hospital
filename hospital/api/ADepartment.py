from ..control.CDepartment import CDepartment
from ..extensions.base_resource import Resource


class ADepartment(Resource):

    def __init__(self):
        self.cdepartment = CDepartment()

    def get(self, department):
        apis = {
            'get': self.cdepartment.get,
            'list': self.cdepartment.list,
            'list_sympotom': self.cdepartment.list_sympotom,
            'get_sympotom': self.cdepartment.get_sympotom,
        }
        return apis

    def post(self, department):
        apis = {
            'add_or_update_dep': self.cdepartment.add_or_update_dep
        }
        return apis
