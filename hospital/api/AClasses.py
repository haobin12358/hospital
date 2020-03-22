# -*- coding : utf-8 -*-
from hospital.extensions.base_resource import Resource
from hospital.control.CClasses import CClasses

class AClasses(Resource):
    def __init__(self):
        self.cclasses = CClasses()

    def get(self, classes):
        apis = {
            "list": self.cclasses.list,
            "get": self.cclasses.get
        }

        return apis

    def post(self, classes):
        apis = {
            "set_class": self.cclasses.set_class,
            "set_course": self.cclasses.set_course
        }

        return apis