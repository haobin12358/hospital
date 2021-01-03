# -*- coding: utf-8 -*-
import math
import os
import uuid
from datetime import datetime
import sys

sys.path.append('..')
from PIL import Image as img
from PIL import ImageFont as imf
from PIL import ImageDraw as imd

import requests
from flask import current_app
from sqlalchemy import false, func

from hospital.config.enums import EvaluationPointLevel
from hospital.config.secret import ALIOSS_ENDPOINT
from hospital.extensions.register_ext import wx_server, db
import base64

from hospital.models import SharingParameters, User, Answer, EvaluationItem, EvaluationAnswer, AnswerItem, \
    EvaluationPoint, Evaluation


class Wxacode():
    def wxacode_unlimit(self, usid, scene=None, img_name=None, **kwargs):
        """
        生成带参数的小程序码
        :param usid: 用户id
        :param scene: 需要携带的参数，dict型参数
        :param img_name: 图片名，同一日再次生成同名图片会被替换
        """
        savepath, savedbpath = self._get_path('qrcode')
        secret_usid = self._base_encode(usid)
        if not img_name:  # 默认图片名称，再次生成会替换同名图片
            img_name = secret_usid
        filename = os.path.join(savepath, '{}.jpg'.format(img_name))
        filedbname = os.path.join(savedbpath, '{}.jpg'.format(img_name))
        current_app.logger.info('filename: {} ; filedbname: {}'.format(filename, filedbname))
        if not scene:
            scene = {'params': self.shorten_parameters('secret_usid={}'.format(secret_usid), usid, 'params')}
        scene_str = self.dict_to_query_str(scene)
        current_app.logger.info('get scene str: {}'.format(scene_str))
        try:
            with open(filename, 'wb') as f:
                buffer = wx_server.get_wxacode_unlimit(scene_str, **kwargs)
                if len(buffer) < 500:
                    current_app.logger.error('buffer error：{}'.format(buffer))
                    filedbname = None
                f.write(buffer)
        except Exception as e:
            current_app.logger.error('生成个人小程序码失败：{}'.format(e))
            filedbname = None

        # # 二维码上传到oss
        # from hospital.control.CFile import CFile
        # CFile().upload_to_oss(filename, filedbname[1:], '头像')
        return filedbname

    def uploadoss(self, filename, filedbname, msg=''):

        # 二维码上传到oss
        from hospital.control.CFile import CFile
        CFile().upload_to_oss(filename, filedbname[1:], msg)

    @staticmethod
    def _get_path(fold):
        """获取服务器上文件路径"""
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        filepath = os.path.join(current_app.config['BASEDIR'], 'img', fold, year, month, day)
        file_db_path = os.path.join('/img', fold, year, month, day)
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
        return filepath, file_db_path

    @staticmethod
    def _base_encode(raw):
        raw = raw.encode()
        return base64.b64encode(raw).decode()

    @staticmethod
    def dict_to_query_str(kwargs):
        """
        :param kwargs: {'name':'python'， ‘age’:30}
        :return 'name=python&age=30'
        """
        if not isinstance(kwargs, dict):
            return
        return '&'.join(map(lambda x: '{}={}'.format(x, kwargs.get(x)), kwargs.keys()))

    @staticmethod
    def shorten_parameters(raw, usid, raw_name):
        """
        缩短分享参数
        :param raw: 要分享的参数
        :param usid: 用户id
        :param raw_name: 分享参数名
        :return: 缩短后的参数
        """
        spsid = db.session.query(SharingParameters.SPSid).filter(
            SharingParameters.SPScontent == raw, SharingParameters.USid == usid,
            SharingParameters.SPSname == raw_name).scalar()
        current_app.logger.info('exist spsid : {}'.format(spsid))
        if not spsid:
            with db.auto_commit():
                sps = SharingParameters.create({'USid': usid, 'SPScontent': raw, 'SPSname': raw_name})
                db.session.add(sps)
            spsid = sps.SPSid
        return spsid


class Share(Wxacode):

    def __init__(self, usid, point, answer):
        super(Share, self).__init__()
        self.resource_path = os.path.join(current_app.config['BASEDIR'], 'hospital', 'extensions', 'share')
        self.background = os.path.join(self.resource_path, 'bg.png')
        self.gh = os.path.join(self.resource_path, 'gh.png')
        self.yy = os.path.join(self.resource_path, 'yy.png')
        self.usid = usid
        self.user = User.query.filter(User.isdelete == false(), User.USid == self.usid).first()
        current_app.logger.info('get point = {}'.format(point))
        self.point = point
        self.answer = answer
        tmppath, tmpdbpath = self._get_path('tmp')

        self.path = os.path.join(tmppath, '{}.png'.format(answer.ANid))
        self.dbpath = os.path.join(tmpdbpath, '{}.png'.format(answer.ANid))

    def drawshare(self, ):
        # answer = Answer.query.filter(Answer.isdelete == false(), Answer.USid == self.usid, Answer.ANid == anid).first()
        ep = self.get_evaluation_point()
        if not ep:
            return ''
        eplevel = ep.EPshareLevel
        current_app.logger.info('get level {}'.format(eplevel))
        try:
            if int(eplevel) == EvaluationPointLevel.good.value:
                # 良好
                if self.draw_good(ep):
                    return self.dbpath
                return ''
            elif int(eplevel) == EvaluationPointLevel.attention.value:
                current_app.logger.info('get level {}'.format(eplevel))
                if self.draw_warn(ep):
                    return self.dbpath
                return ''
            elif int(eplevel) == EvaluationPointLevel.vigilant.value:

                if self.draw_vigilant(ep):
                    return self.dbpath
                return ''
            else:
                return ''
        except Exception as e:
            current_app.logger.error('get error = {}'.format(e))
            return ''

    def get_wxac(self):
        with db.auto_commit():
            if not self.user.USwxac:

                wxacpath = self.wxacode_unlimit(self.usid)
                self.user.USwxac = wxacpath
            else:
                wxacpath = self.user.USwxac
            wxac = os.path.join(current_app.config['BASEDIR'], wxacpath[1:])
            if os.path.isfile(wxac):
                return wxac
            headurl = ALIOSS_ENDPOINT + self.user.USwxac
            try:
                data = requests.get(headurl)
                with open(wxac, 'wb') as head:
                    head.write(data.content)
                return wxac
            except Exception as e:
                current_app.logger.error('get avatar error usid = {} exception = {}'.format(self.usid, e))
                return ''

    def get_avatar(self):
        avatar = os.path.join(current_app.config['BASEDIR'], self.user.USavatar[1:])
        if os.path.isfile(avatar):
            return avatar
        headurl = ALIOSS_ENDPOINT + self.user.USavatar
        try:
            data = requests.get(headurl)
            with open(avatar, 'wb') as head:
                head.write(data.content)
            return avatar
        except Exception as e:
            current_app.logger.error('get avatar error usid = {} exception = {}'.format(self.usid, e))
            return ''

    def get_evaluation_point(self):
        evaluationpoint = EvaluationPoint.query.filter(
            EvaluationPoint.EPstart <= self.point, EvaluationPoint.EVid == self.answer.EVid,
            EvaluationPoint.EPend >= self.point, EvaluationPoint.isdelete == 0).first()
        return evaluationpoint

    def get_evaluation_args(self):
        evaluation = Evaluation.query.filter(
            Evaluation.EVid == self.answer.EVid, Evaluation.isdelete == false()).first()
        if not evaluation:
            return '', 0
        evaluation_len = db.session.query(func.count(Answer.ANid)).filter(
            Answer.EVid == self.answer.EVid, Answer.isdelete == false()).scalar() or 0
        return evaluation.EVname, evaluation_len

    def draw_good(self, ep):
        epaward = ep.EPaward
        base_im, dw = self.draw_base(ep)
        # 良好特殊元素奖励语
        award_font = imf.truetype(os.path.join(self.resource_path, '汉仪综艺体简.ttf'), 42)
        dw.text((178, 978), epaward, font=award_font, fill='#FF0404')
        self.draw_bottom(ep, base_im, dw)
        base_im.save(self.path)
        self.uploadoss(self.path, self.dbpath, '分享图')
        return True

    @staticmethod
    def resize_img(filepath, x, y):
        # time_now = datetime.now()
        # year = str(time_now.year)
        # month = str(time_now.month)
        # day = str(time_now.day)
        # shuffix = os.path.splitext(filepath)[-1]
        # temp_path = os.path.join(current_app.config['BASEDIR'], 'img', 'tmp', year, month, day, 'temp{}.{}'.format(
        #     str(uuid.uuid1()), shuffix))
        tmp_im = img.open(filepath)
        tmp_x, tmp_y = tmp_im.size
        if tmp_x == x and tmp_y == y:
            return tmp_im
        # tmp_im.resize((x, y), img.LANCZOS).save(temp_path)
        # tmp_im = img.open(temp_path)
        return tmp_im.resize((x, y))

    @staticmethod
    def match_text(words, max_width):
        old_list = str(words).split('\n')
        new_list = []

        for p in old_list:
            p_list = list(p)
            if len(p_list) > max_width:
                times = math.ceil(len(p_list) / max_width)
                for i in range(1, times + 1):
                    p_list.insert(max_width * i, '\n')
            new_list.append(''.join(p_list))

        return '\n'.join(new_list)

    def draw_warn(self, ep):
        base_im, dw = self.draw_base(ep)

        # 特殊元素 预购卡片
        dw.rectangle((94, 948, 312, 1050), '#F6A17A')
        dw.rectangle((336, 948, 632, 1050), '#1E9E30')

        icon_im = img.open(self.yy)
        layer = img.new('RGBA', base_im.size, (0, 0, 0, 0))
        layer.paste(icon_im, (116, 978))
        base_im = img.composite(layer, base_im, layer)
        dw = imd.Draw(base_im)
        # 文案
        wenanfont = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 30)
        dw.text((166, 984), '预约推荐', font=wenanfont, fill='#FFFFFF')
        dw.text((364, 966), '凭此测评结果可现\n场免费体验一节课', font=wenanfont, fill='#FFFFFF')

        self.draw_bottom(ep, base_im, dw)
        base_im.save(self.path)
        self.uploadoss(self.path, self.dbpath, '分享图')
        return True

    def draw_vigilant(self, ep):
        base_im, dw = self.draw_base(ep)
        # 特殊元素 预购卡片
        dw.rectangle((94, 948, 312, 1050), '#F6A17A')
        dw.rectangle((336, 948, 632, 1050), '#1E9E30')

        icon_im = img.open(self.gh)
        layer = img.new('RGBA', base_im.size, (0, 0, 0, 0))
        layer.paste(icon_im, (116, 984))
        base_im = img.composite(layer, base_im, layer)
        dw = imd.Draw(base_im)

        # 文案
        wenanfont = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 30)
        dw.text((166, 984), '预约挂号', font=wenanfont, fill='#FFFFFF')
        dw.text((356, 984), '坐诊医生:{}'.format(ep.DOname), font=wenanfont, fill='#FFFFFF')

        self.draw_bottom(ep, base_im, dw)
        base_im.save(self.path)
        self.uploadoss(self.path, self.dbpath, '分享图')
        return True

    def draw_base(self, ep):
        avatar = self.get_avatar()
        if not avatar:
            return ''
        # wxac = self.get_wxac()
        if not avatar:
            return ''
        title, epanalysis, epet, sharewords = ep.EPtitle, ep.EPanalysis, ep.EPevaluation, ep.EPshareWords
        if not (title and epanalysis and epet and sharewords):
            return ''
        bg_im = img.open(self.background)
        width, height = bg_im.size
        base_im = img.new('RGB', (width, height), color=(255, 255, 0, 0))
        # 背景图
        base_im.paste(bg_im, (0, 0))
        dw = imd.Draw(base_im)
        # 头像
        avatar_im = self.resize_img(avatar, 120, 120)
        avatar_mask = img.new('RGBA', (120, 120), color=(0, 0, 0, 0))
        mask_draw = imd.Draw(avatar_mask)
        mask_draw.ellipse((0, 0, 120, 120), fill=(159, 159, 160))
        base_im.paste(avatar_im, (34, 66), avatar_mask)
        # 昵称
        namefont = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Medium.otf'), 32)
        dw.text((178, 76), '尊敬的{}家长'.format(self.user.USname), font=namefont, fill='#FFFFFF')
        # 问卷名和排名
        evname, evlen = self.get_evaluation_args()
        evfont = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 26)
        evwords = self.match_text('您是第{}个参与了“{}”在线测试的，根据你的测试结果如下：'.format(evlen + 1, evname), 22)

        dw.text((178, 126), evwords, font=evfont, fill='#FFFFFF')
        # 大标题
        title_font = imf.truetype(os.path.join(self.resource_path, 'SOURCEHANSANSSC-BOLD.OTF'), 48)
        dw.text((274, 300), title, font=title_font, fill='#FF0000')
        # 固定文字：
        itemwords = '孩子的得分情况:\n初步分析:\n评估建议:\n'
        itemfont = imf.truetype(os.path.join(self.resource_path, 'SOURCEHANSANSSC-BOLD.OTF'), 28)
        dw.text((130, 384), itemwords, font=itemfont, fill='#000000')
        # 得分数值
        pointfont = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 28)
        dw.text((354, 386), str(self.point), font=pointfont, fill='#FF0404')

        # 初步分析：
        analy_font = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 28)
        dw.text((266, 424), epanalysis, font=analy_font, fill='#FF0404')

        # 评估建议
        epet_font = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 26)
        dw.text((130, 512), self.match_text(epet, 18), font=epet_font, fill='#000000')
        return base_im, dw

    def draw_bottom(self, ep, base_im, dw):

        # 小程序码
        wxac = self.get_wxac()
        wxac_im = self.resize_img(wxac, 162, 162)
        base_im.paste(wxac_im, (38, 1080))

        # 邀请好友一起测评
        invite_font = imf.truetype(os.path.join(self.resource_path, 'SourceHanSerifCN-Bold.otf'), 40)
        dw.text((222, 1096), '邀请好友一起测评', font=invite_font, fill='#000000')

        # 分享语
        sharewords_font = imf.truetype(os.path.join(self.resource_path, 'SourceHanSansSC-Regular.otf'), 24)

        dw.text((212, 1150), self.match_text(ep.EPshareWords, 21), font=sharewords_font, fill='#000000')


if __name__ == '__main__':
    from hospital import create_app

    app = create_app()
    with app.app_context():
        answer = Answer.query.filter(Answer.ANid == 'cb45978e-e55b-11ea-b841-fa163e8df331').first()
        share = Share(answer.USid, 4, answer)
        print(share.drawshare())
