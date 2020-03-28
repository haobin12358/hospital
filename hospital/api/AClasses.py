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
            "get_course_by_doctor_ampm": self.cclasses.get_course_by_doctor_ampm,
            "get_setmeal": self.cclasses.get_setmeal,
            "get_subscribe_list": self.cclasses.get_subscribe_list
        }

        return apis

    def post(self, classes):
        apis = {
            "set_class": self.cclasses.set_class,
            "set_course": self.cclasses.set_course,
            "delete_course": self.cclasses.delete_course,
            "subscribe_classes": self.cclasses.subscribe_classes,
            "set_setmeal": self.cclasses.set_setmeal,
            "update_sustatus": self.cclasses.update_sustatus
        }

        return apis