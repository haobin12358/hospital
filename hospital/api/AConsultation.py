from ..control.CConsultation import CConsultation
from ..extensions.base_resource import Resource


class AConsultation(Resource):

    def __init__(self):
        self.cconsultation = CConsultation()

    def get(self, consultation):
        apis = {
            'list': self.cconsultation.list,
            'list_enroll': self.cconsultation.list_enroll,
        }
        return apis

    def post(self, consultation):
        apis = {
            'add_enroll': self.cconsultation.add_enroll,
            'add_or_update_consultation': self.cconsultation.add_or_update_consultation,
        }
        return apis
