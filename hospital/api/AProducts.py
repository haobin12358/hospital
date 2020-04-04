from ..extensions.base_resource import Resource
from ..control.CProducts import CProducts


class AProducts(Resource):
    def __init__(self):
        self.cproducts = CProducts()

    def get(self, product):
        apis = {
            'list': self.cproducts.list,
            'get': self.cproducts.get
        }
        return apis

    def post(self, product):
        apis = {
            'add_or_update_product': self.cproducts.add_or_update_product,
            'batch_operation': self.cproducts.batch_operation,
        }
        return apis
