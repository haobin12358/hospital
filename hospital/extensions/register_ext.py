# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy
from hospital.extensions.aliyunoss.storage import AliyunOss
from .query_session import Query
from hospital.config.secret import DB_PARAMS, SERVICE_APPID, SERVICE_APPSECRET, server_dir, ACCESS_KEY_ID, \
    ACCESS_KEY_SECRET, ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT
from .loggers import LoggerHandler
from .weixin.mp import WeixinMP


class SQLAlchemy(_SQLAlchemy):
    def init_app(self, app):
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', DB_PARAMS)
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
        # app.config.setdefault('SQLALCHEMY_ECHO', True)  # 开启sql日志
        super(SQLAlchemy, self).init_app(app)

    @contextmanager
    def auto_commit(self):
        try:
            yield db.session
            self.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


db = SQLAlchemy(query_class=Query, session_options={"expire_on_commit": False, "autoflush": False})

wx_server = WeixinMP(SERVICE_APPID, SERVICE_APPSECRET,
                     ac_path=os.path.join(server_dir, ".access_token"),
                     jt_path=os.path.join(server_dir, ".jsapi_ticket"))

ali_oss = AliyunOss(ACCESS_KEY_ID, ACCESS_KEY_SECRET, ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT)


def register_ext(app, logger_file='/tmp/hospital/'):
    db.init_app(app)
    LoggerHandler(app, file=logger_file).error_handler()
