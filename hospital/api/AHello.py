from ..control.CHello import CHello
from ..extensions.base_resource import Resource


class AHello(Resource):
    def __init__(self):
        self.chello = CHello()

    def get(self, hello):
        apis = {
            'get': self.chello.hello
        }
        return apis
