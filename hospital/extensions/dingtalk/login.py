# -*- coding: utf-8 -*-
import os
import json
import time
import string
import random
import hashlib
import requests

from .base import DingtalkError, Map

DEFAULT_DIR = os.getenv("HOME_EP", os.getcwd())
headers = {
    "Content-type": "application/json;charset=UTF-8",
    "Cache-Control": "no-cache",
    "Connection": "Keep-Alive",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
}


class DingtalkLoginError(DingtalkError):

    def __init__(self, msg):
        super(DingtalkLoginError, self).__init__(msg)


class DingtalkLogin(object):

    def __init__(self, app_key, app_secret, agent_id, corp_id, jt_path=None, ac_path=None):
        self.sess = requests.Session()
        self.app_key = app_key
        self.app_secret = app_secret
        self.agent_id = agent_id
        self.corp_id = corp_id
        if jt_path is None:
            jt_path = os.path.join(DEFAULT_DIR, ".dingtalk_jsapi_ticket")
        self.jt_path = jt_path
        if ac_path is None:
            ac_path = os.path.join(DEFAULT_DIR, ".dingtalk_access_token")
        self.ac_path = ac_path

    def _get(self, url, params):
        resp = self.sess.get(url, params=params, headers=headers)
        data = Map(json.loads(resp.content.decode("utf-8")))
        if data.errcode:
            msg = "%(errcode)d %(errmsg)s" % data
            raise DingtalkLoginError(msg)
        return data

    @property
    def access_token(self):
        timestamp = time.time()
        if not os.path.exists(self.ac_path) or \
                int(os.path.getmtime(self.ac_path)) < timestamp:
            params = dict()
            params.setdefault("appkey", self.app_key)
            params.setdefault("appsecret", self.app_secret)
            data = self._get("https://oapi.dingtalk.com/gettoken", params)
            with open(self.ac_path, 'wb') as fp:
                fp.write(data.access_token.encode("utf-8"))
            os.utime(self.ac_path, (timestamp, timestamp + data.expires_in - 600))
        return open(self.ac_path).read().strip()

    def user_id(self, code):
        url = "https://oapi.dingtalk.com/user/getuserinfo"
        args = dict()
        args.setdefault("access_token", self.access_token)
        args.setdefault("code", code)

        return self._get(url, args)

    def user_info(self, user_id):
        url = "https://oapi.dingtalk.com/user/get"
        args = dict()
        args.setdefault("access_token", self.access_token)
        args.setdefault("userid", user_id)
        args.setdefault("lang", "zh_CN")

        return self._get(url, args)

    @property
    def nonce_str(self):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    @property
    def jsapi_ticket(self):
        timestamp = time.time()
        if not os.path.exists(self.jt_path) or \
                int(os.path.getmtime(self.jt_path)) < timestamp:
            params = dict()
            params.setdefault("access_token", self.access_token)
            data = self._get("https://oapi.dingtalk.com/get_jsapi_ticket", params)
            with open(self.jt_path, 'wb') as fp:
                fp.write(data.ticket.encode("utf-8"))
            os.utime(self.jt_path, (timestamp, timestamp + data.expires_in - 600))
        return open(self.jt_path).read()

    def jsapi_sign(self, **kwargs):
        """
        生成签名给js使用
        """
        timestamp = str(int(time.time()))
        nonce_str = self.nonce_str
        kwargs.setdefault("jsapi_ticket", self.jsapi_ticket)
        kwargs.setdefault("timestamp", timestamp)
        kwargs.setdefault("noncestr", nonce_str)
        kwargs.setdefault("url", kwargs.get("url"))
        raw = [(k, kwargs[k]) for k in sorted(kwargs.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        sign = hashlib.sha1(s.encode("utf-8")).hexdigest().lower()
        return Map(signature=sign, timeStamp=timestamp, nonceStr=nonce_str, corpId=self.corp_id,
                   agentId=self.agent_id)
