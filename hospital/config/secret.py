# -*- coding: utf-8 -*-
import os
from .http_config import API_HOST

env = os.environ
BASEDIR = os.path.abspath(os.path.join(__file__, '../../../'))

# db
database = env.get('EP_DB_NAME', "epsoft")
host = env.get('EPSOFT_DB_HOST', "127.0.0.1")
port = "3306"
username = env.get('EPSOFT_DB_USER', '')
password = env.get('EPSOFT_DB_PWD', 'password')
charset = "utf8mb4"
sqlenginename = 'mysql+pymysql'
DB_PARAMS = "{0}://{1}:{2}@{3}/{4}?charset={5}".format(
    sqlenginename,
    username,
    password,
    host,
    database,
    charset)

# 微信
appid = env.get('EPAPPID', '')
appsecret = env.get('EPAPPSECRET', '')
wxtoken = env.get('WXTOKEN', '')
wxscope = 'snsapi_userinfo'
mch_id = env.get('MCH_ID')
mch_key = env.get('MCH_KEY')
apiclient_cert = os.path.join(BASEDIR, 'pem', 'apiclient_cert.pem')
apiclient_key = os.path.join(BASEDIR, 'pem', 'apiclient_key.pem')
apiclient_public = os.path.join(BASEDIR, 'pem', 'apiclient_public.pem')

# 服务号
SERVICE_APPID = env.get('EP_SERVICE_APPID', 'wx4713189bca688f2f')
SERVICE_APPSECRET = env.get('EP_SERVICE_APPSECRET', 'b89fb5433670ba2abd7cd0cb85ca93cc')
server_dir = os.path.join(BASEDIR, 'wxserver')

# 小程序
MiniProgramAppId = env.get('MINI_PROGRAM_APPID', 'wx92494019ca305b1d')
MiniProgramAppSecret = env.get('MINI_PROGRAM_APPSECRCT', '')
MiniProgramWxpay_notify_url = API_HOST + '/api/v2/play/wechat_notify'


# 模板推送备用账号
testopenid = "o1df8wc2Yqjlk9YmcSJKZtHr"

class DefaltSettig(object):
    SECRET_KEY = env.get('SECRET', 'guess')
    TOKEN_EXPIRATION = 3600 * 7 * 24  # token过期时间(秒)
    DEBUG = True
    BASEDIR = BASEDIR
