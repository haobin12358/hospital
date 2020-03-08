from datetime import datetime

from epsoft.config.enums import TestEnum
from epsoft.extensions.success_response import Success


class CHello(object):
    def hello(self):
        return Success(data="{}, {}, {}".format(TestEnum.ok.value, TestEnum.ok.zh_value, datetime.now()))
