# -*- coding : utf-8 -*-
from ..control.CAssistance import CAssistance
from ..extensions.base_resource import Resource


class AAssistance(Resource):
    def __init__(self):
        self.cassistance = CAssistance()

    def get(self, assistance):
        apis = {
            'list_relatives': self.cassistance.list_relatives,
            'relatives': self.cassistance.relatives,
            'relatives_type': self.cassistance.relatives_type,

        }
        return apis

    def post(self, assistance):
        apis = {
            'set_relatives': self.cassistance.set_relatives,
        }

        return apis
