# -*- coding : utf-8 -*-
from hospital.extensions.base_resource import Resource
from hospital.control.CEvaluation import CEvaluation

class AEvaluation(Resource):
    def __init__(self):
        self.cevaluation = CEvaluation()

    def get(self, evaluation):
        apis = {
            "list": self.cevaluation.list,
            "get": self.cevaluation.get
        }

        return apis

    def post(self, evaluation):
        apis = {
            "set_evaluation": self.cevaluation.set_evaluation,
            "set_evaluationitem": self.cevaluation.set_evaluationitem,
            "set_evaluationanswer": self.cevaluation.set_evaluationanswer,
            "set_evaluationpoint": self.cevaluation.set_evaluationpoint,
            "make_evaluation": self.cevaluation.make_evaluation
        }

        return apis