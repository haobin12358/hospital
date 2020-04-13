# -*- coding: utf-8 -*-
from flask import current_app, request
import uuid

from hospital.config.enums import PointTaskType
from hospital.extensions.interface.user_interface import doctor_required, token_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Series, Video


class CVideo(object):
    def __init__(self):
        pass

    @doctor_required
    def add_or_update_series(self):
        data = parameter_required()
        seid = data.get('seid')
        doid = getattr(request, 'user').id
        with db.auto_commit():
            if seid:
                series = Series.query.filter(
                    Series.SEid == seid, Series.isdelete == 0).first()
                current_app.logger.info('get series {} '.format(series))
                # 优先判断删除
                if data.get('delete'):
                    if not series:
                        raise ParamsError('剧集已删除')
                    current_app.logger.info('删除科室 {}'.format(doid))
                    series.isdelete = 1
                    db.session.add(series)
                    return Success('删除成功', data=seid)

                # 执行update
                if series:
                    update_dict = series.get_update_dict(data)
                    if update_dict.get('SEid'):
                        update_dict.pop('SEid')
                    if update_dict.get('DOid'):
                        update_dict.pop('DOid')
                    if update_dict.get('SEsort', 0):
                        try:
                            int(update_dict.get('SEsort'))
                        except:
                            raise ParamsError('排序请输入整数')

                    series.update(update_dict)
                    current_app.logger.info('更新系列 {}'.format(seid))
                    db.session.add(series)
                    return Success('更新成功', data=seid)
            # 添加
            data = parameter_required({'sename': '剧集名', })

            seid = str(uuid.uuid1())

            if data.get('sesort', 0):
                try:
                    int(data.get('sesort', 0))
                except:
                    raise ParamsError('排序请输入整数')
            doctor = Series.create({
                'DOid': doid,
                'SEid': seid,
                'SEname': data.get('sename'),
                'SEsort': data.get('sesort', 0),
            })
            current_app.logger.info('创建剧集 {}'.format(data.get('sename')))
            db.session.add(doctor)
        return Success('创建剧集成功', data=doid)

    @doctor_required
    def list_series(self):
        data = parameter_required()
        doid = getattr(request, 'user').id
        sename = data.get('sename')
        filter_args = [Series.isdelete == 0, Series.DOid == doid]
        if sename:
            filter_args.append(Series.SEname.ilike('%{}%'.format(sename)))
        series_list = Series.query.filter(*filter_args).order_by(
            Series.SEsort.asc(), Series.createtime.desc()).all_with_page()
        return Success('获取成功', data=series_list)

    @doctor_required
    def get_series(self):
        data = parameter_required('seid')
        seid = data.get('seid')
        series = Series.query.filter(Series.SEid == seid, Series.isdelete == 0).first_('剧集已删除')
        video_list = Video.query.filter(Video.SEid == series.SEid, Video.isdelete == 0).order_by(
            Video.VIsort.asc(), Video.createtime.desc()).all()
        series.fill('videos', video_list)
        return Success("获取成功", data=series)

    @doctor_required
    def add_or_update_video(self):
        data = parameter_required()
        viid = data.get('viid')
        doid = getattr(request, 'user').id
        with db.auto_commit():
            if viid:
                video = Video.query.filter(
                    Video.VIid == viid, Video.isdelete == 0).first()
                current_app.logger.info('get video {} '.format(video))
                # 优先判断删除
                if data.get('delete'):
                    if not video:
                        raise ParamsError('视频已删除')
                    current_app.logger.info('删除视频 {}'.format(doid))
                    video.isdelete = 1
                    db.session.add(video)
                    return Success('删除成功', data=viid)

                # 执行update
                if video:
                    update_dict = video.get_update_dict(data)
                    if update_dict.get('VIid'):
                        update_dict.pop('VIid')
                    if update_dict.get('DOid'):
                        update_dict.pop('DOid')
                    if update_dict.get('VIsort', 0):
                        try:
                            int(update_dict.get('VIsort'))
                        except:
                            raise ParamsError('排序请输入整数')

                    video.update(update_dict)
                    current_app.logger.info('更新视频 {}'.format(viid))
                    db.session.add(video)
                    return Success('更新成功', data=viid)
            # 添加
            data = parameter_required({
                'viname': '剧集名',
                'vimedia': '视频路由',
                'vidur': '视频时长',
                'vithumbnail': '视频缩略图', })

            viid = str(uuid.uuid1())

            if data.get('visort', 0):
                try:
                    int(data.get('visort', 0))
                except:
                    raise ParamsError('排序请输入整数')
            doctor = Video.create({
                'DOid': doid,
                'VIid': viid,
                'VIname': data.get('viname'),
                'VImedia': data.get('vimedia'),
                'VIthumbnail': data.get('vithumbnail'),
                'SEid': data.get('seid'),
                'VIdur': data.get('vidur'),
                'VIbriefIntroduction': data.get('vibriefintroduction'),
                'VIsort': data.get('visort', 0),
            })
            current_app.logger.info('创建视频 {}'.format(data.get('viname')))
            db.session.add(doctor)
        return Success('创建视频成功', data=viid)

    @token_required
    def get_video(self):
        data = parameter_required('viid')
        viid = data.get('viid')
        usid = getattr(request, 'user').id
        video = Video.query.filter(Video.VIid == viid, Video.isdelete == 0).first_('视频已删除')
        if video.SEid:
            se_video_list = Video.query.filter(Video.SEid == video.SEid, Video.isdelete == 0).order_by(
                Video.VIsort.asc(), Video.createtime.desc()).all()
            sename_list = [{'viid': se_video.VIid, 'viname': '第{}期：{}'.format(i + 1, se_video.VIname)}
                           for i, se_video in enumerate(se_video_list)]
            video.fill('senamelist', sename_list)
            series = Series.query.filter(Series.SEid == video.SEid, Series.isdelete == 0).first()
            if series:
                video.fill('sename', series.SEname)
        # 添加积分获取
        from .CConfig import CConfig
        CConfig()._judge_point(PointTaskType.watch_video.value, 1, usid)

        return Success('获取成功', data=video)

    def list_video(self):
        data = parameter_required()
        doid = data.get('doid')
        seid = data.get('seid')
        viname = data.get('viname')
        filter_args = [Video.isdelete == 0, ]
        order_by_args = [Video.createtime.desc()]
        if doid:
            filter_args.append(Video.DOid == doid)
        if seid:
            order_by_args.insert(0, Video.VIsort.asc())
            filter_args.append(Video.SEid == seid)
        if viname:
            filter_args.append(Video.VIname.ilike('%{}%'.format(viname)))

        video_list = Video.query.filter(*filter_args).order_by(*order_by_args).all_with_page()

        return Success('获取成功', data=video_list)
