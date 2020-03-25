# -*- coding : utf-8 -*-
from ..control.CVideo import CVideo
from ..extensions.base_resource import Resource


class AVideo(Resource):
    def __init__(self):
        self.cvideo = CVideo()

    def get(self, video):
        apis = {
            'get_video': self.cvideo.get_video,
            'get_series': self.cvideo.get_series,
            'list_series': self.cvideo.list_series,
            'list_video': self.cvideo.list_video,
        }
        return apis

    def post(self, video):
        apis = {
            'add_or_update_series': self.cvideo.add_or_update_series,
            'add_or_update_video': self.cvideo.add_or_update_video,
        }
        return apis
