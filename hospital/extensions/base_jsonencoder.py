from datetime import datetime, date
from decimal import Decimal

from flask.json import JSONEncoder as _JSONEncoder
from werkzeug.exceptions import HTTPException


class JSONEncoder(_JSONEncoder):
    """重写对象序列化, 当默认jsonify无法序列化对象的时候将调用这里的default"""

    def default(self, o):

        if hasattr(o, 'keys') and hasattr(o, '__getitem__'):
            res = dict(o)
            new_res = {k.lower(): v for k, v in res.items()}
            return new_res
        if isinstance(o, datetime):
            # 也可以序列化时间类型的对象
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        if isinstance(o, type):
            raise o()
        if isinstance(o, HTTPException):
            raise o
        if isinstance(o, Decimal):
            return round(float(o), 2)
        raise TypeError(repr(o) + " is not JSON serializable")
