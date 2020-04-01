# -*- coding : utf-8 -*-
from ..control.CReview import CReview
from ..extensions.base_resource import Resource


class AReview(Resource):
    def __init__(self):
        self.creview = CReview()

    def get(self, review):
        apis = {
            'get_review': self.creview.get_review
        }
        return apis

    def post(self, review):
        apis = {
            'set_review': self.creview.set_review,
            "delete": self.creview.delete
        }

        return apis