# -*- coding: utf-8 -*-
from flask import Flask
from flask import Blueprint
from flask_cors import CORS

from .api import AAssistance
from .api.AFile import AFile
from .api.AHello import AHello
from .api.AConfig import AConfig
from .api.AAdmin import AAdmin
from .api.ADoctor import ADoctor
from .api.ADepartment import ADepartment
from .api.AClasses import AClasses
from .api.AUser import AUser
from .api.AVideo import AVideo
from .api.AExample import AExample
from .api.AEvaluation import AEvaluation
from .extensions.request_handler import error_handler, request_first_handler
from .config.secret import DefaltSettig
from .extensions.register_ext import register_ext
from hospital.extensions.base_jsonencoder import JSONEncoder
from hospital.extensions.base_request import Request


def register(app):
    bp = Blueprint(__name__, 'bp', url_prefix='/api')
    bp.add_url_rule('/hello/<string:hello>', view_func=AHello.as_view('hello'))
    bp.add_url_rule('/config/<string:config>', view_func=AConfig.as_view('config'))
    bp.add_url_rule('/admin/<string:admin>', view_func=AAdmin.as_view('admin'))
    bp.add_url_rule('/doctor/<string:doctor>', view_func=ADoctor.as_view('doctor'))
    bp.add_url_rule('/department/<string:department>', view_func=ADepartment.as_view('department'))
    bp.add_url_rule('/classes/<string:classes>', view_func=AClasses.as_view('classes'))
    bp.add_url_rule('/user/<string:user>', view_func=AUser.as_view('user'))
    bp.add_url_rule('/file/<string:file>', view_func=AFile.as_view('file'))
    bp.add_url_rule('/example/<string:example>', view_func=AExample.as_view('example'))
    bp.add_url_rule('/video/<string:video>', view_func=AVideo.as_view('video'))
    bp.add_url_rule('/evaluation/<string:evaluation>', view_func=AEvaluation.as_view('evaluation'))
    bp.add_url_rule('/assistance/<string:assistance>', view_func=AAssistance.as_view('assistance'))
    app.register_blueprint(bp)


def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    return resp


def create_app():
    app = Flask(__name__)
    app.json_encoder = JSONEncoder
    app.request_class = Request
    app.config.from_object(DefaltSettig)
    app.after_request(after_request)
    register(app)
    CORS(app, supports_credentials=True)
    request_first_handler(app)
    register_ext(app)
    error_handler(app)
    return app
