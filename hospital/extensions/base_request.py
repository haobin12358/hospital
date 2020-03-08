import json

from flask import Request as _Request, current_app


class Request(_Request):
    def on_json_loading_failed(self, e):
        from .error_response import ParamsError
        if current_app is not None and current_app.debug:
            raise ParamsError('Failed to decode JSON object: {0}'.format(e))
        raise ParamsError('参数异常')

    def get_json(self, force=False, silent=False, cache=True):
        data = self.data
        if not data:
            return
        try:
            rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
                if cache:
                    normal_rv, _ = self._cached_json
                    self._cached_json = (normal_rv, rv)
            else:
                rv = self.on_json_loading_failed(e)
                if cache:
                    _, silent_rv = self._cached_json
                    self._cached_json = (rv, silent_rv)
        else:
            if cache:
                self._cached_json = (rv, rv)
        return rv

    @property
    def detail(self):
        res = {
            'path': self.path,
            'method': self.method,
            'data': self.data,
            'query': self.args.to_dict(),
            'address': self.remote_addr
        }
        return res

    @property
    def remote_addr(self):
        if 'X-Real-Ip' in self.headers:
            return self.headers['X-Real-Ip']
        return super(Request, self).remote_addr
