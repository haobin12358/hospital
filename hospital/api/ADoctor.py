from ..control.CDoctor import CDoctor
from ..extensions.base_resource import Resource


class ADoctor(Resource):

    def __init__(self):
        self.cdoctor = CDoctor()

    def get(self, doctor):
        apis = {
            'get': self.cdoctor.get,
            'list': self.cdoctor.list,
        }
        return apis

    def post(self, doctor):
        apis = {
            'add_or_update_doctor': self.cdoctor.add_or_update_doctor
        }
        return apis
