# -*- coding : utf-8 -*-
from hospital.extensions.base_resource import Resource
from hospital.control.CClasses import CClasses

class AClasses(Resource):
    def __init__(self):
        self.cclasses = CClasses()

    def get(self, classes):
        apis = {
            "list": self.cclasses.list,
            "get": self.cclasses.get,
            "get_course": self.cclasses.get_course,
            "get_course_by_doctor_month": self.cclasses.get_course_by_doctor_month,
            "get_course_by_doctor_day": self.cclasses.get_course_by_doctor_day,
            "get_course_by_doctor_ampm": self.cclasses.get_course_by_doctor_ampm
        }

        return apis

    def post(self, classes):
        apis = {
            "set_class": self.cclasses.set_class,
            "set_course": self.cclasses.set_course,
            "delete_course": self.cclasses.delete_course,
            "subscribe_classes": self.cclasses.subscribe_classes
        }

        return apis