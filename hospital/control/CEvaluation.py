"""
本文件用于处理问卷逻辑
create user: haobin12358
last update time:2020/3/13 03:53
"""
import uuid
from flask import request, current_app
from decimal import Decimal
from hospital.extensions.interface.user_interface import is_hign_level_admin, is_admin
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import AuthorityError, PointError, EvaluationNumError
from hospital.models.evaluation import Evaluation, EvaluationAnswer, EvaluationItem, EvaluationPoint, Answer, AnswerItem

class CEvaluation:

    def set_evaluation(self):
        """设置问卷主体"""
        data = parameter_required(('evname', 'evpicture', ) if not request.json.get('delete') else('evid',))
        if not (is_hign_level_admin() or is_admin()):
            return AuthorityError()
        ev_dict = {
            "EVname": data.get('evname'),
            "EVpicture": data.get('evpicture')
        }
        evid = data.get("evid")
        with db.auto_commit():
            if not evid:
                # 新增
                ev_dict["EVid"] = str(uuid.uuid1())
                ev_instance = Evaluation.create(ev_dict)
                msg = "新增成功"
            else:
                ev_instance = Evaluation.query.filter(Evaluation.EVid == evid).first_("未找到该问卷")
                if data.get("delete"):
                    ev_instance.update({"isdelete": 1})
                    msg = "删除成功"
                else:
                    ev_instance.update(ev_dict)
                    msg = "修改成功"
            db.session.add(ev_instance)
        return Success(message=msg)

    def set_evaluationitem(self):
        """设置问卷题目"""
        data = parameter_required(('evid', 'einame', 'eiindex', ) if not request.json.get('delete') else('eiid', ))
        if not (is_hign_level_admin() or is_admin()):
            return AuthorityError()
        ei_dict = {
            "EVid": data.get('evid'),
            "EIname": data.get('einame'),
            "EIindex": data.get('eiindex')
        }
        eiid = data.get("eiid")
        with db.auto_commit():
            if not eiid:
                # 新增
                ei_dict["EIid"] = str(uuid.uuid1())
                ei_instance = EvaluationItem.create(ei_dict)
                msg = "新增成功"
            else:
                ei_instance = EvaluationItem.query.filter(EvaluationItem.EIid == eiid).first_("未找到该题目")
                if data.get("delete"):
                    ei_instance.update({"isdelete": 1})
                    msg = "删除成功"
                else:
                    ei_instance.update(ei_dict)
                    msg = "修改成功"
            db.session.add(ei_instance)
        return Success(message=msg)

    def set_evaluationanswer(self):
        """设置题目选项"""
        data = parameter_required(('eiid', 'eaname', 'eaindex', 'eapoint') if not request.json.get('delete') else('eaid',))
        if not (is_hign_level_admin() or is_admin()):
            return AuthorityError()
        ea_dict = {
            "EIid": data.get('eiid'),
            "EAname": data.get('eaname'),
            "EAindex": data.get('eaindex'),
            "EApoint": Decimal(str(data.get('eapoint') or 0))
        }
        eaid = data.get("eaid")
        with db.auto_commit():
            if not eaid:
                # 新增
                ea_dict["EAid"] = str(uuid.uuid1())
                ea_instance = EvaluationAnswer.create(ea_dict)
                msg = "新增成功"
            else:
                ea_instance = EvaluationAnswer.query.filter(EvaluationAnswer.EAid == eaid).first_("未找到该选项")
                if data.get("delete"):
                    ea_instance.update({"isdelete": 1})
                    msg = "删除成功"
                else:
                    ea_instance.update(ea_dict)
                    msg = "修改成功"
            db.session.add(ea_instance)
        return Success(message=msg)

    def set_evaluationpoint(self):
        """设置分数区间"""
        data = parameter_required(('evid', 'epstart', 'epend', 'epanswer') if not request.json.get('delete') else('epid',))
        if not (is_hign_level_admin() or is_admin()):
            return AuthorityError()
        if data.get('epstart') and data.get('epend'):
            epstart = Decimal(str(data.get('epstart') or 0))
            epend = Decimal(str(data.get('epend') or 0))
            if epstart >= epend:
                return PointError("区间大小设置错误")
        else:
            epstart = 0
            epend = 0
        ep_dict = {
            "EVid": data.get('evid'),
            "EPstart": epstart,
            "EPend": epend,
            "EPanswer": data.get('epanswer')
        }
        epid = data.get("epid")
        if data.get('evid'):
            filter_args = [EvaluationPoint.EVid == data.get('evid'), EvaluationPoint.isdelete == 0]
            if epid:
                filter_args.append(EvaluationPoint.EPid != epid)
            ep_list = EvaluationPoint.query.filter(*filter_args).all()
            for ep in ep_list:
                if not(epstart > Decimal(str(ep["EPend"] or 0)) or epend < Decimal(str(ep["EPstart"]) or 0)):
                    return PointError('存在重叠分数区间')
        with db.auto_commit():
            if not epid:
                # 新增
                ep_dict["EPid"] = str(uuid.uuid1())
                ep_instance = EvaluationPoint.create(ep_dict)
                msg = "新增成功"
            else:
                ep_instance = EvaluationPoint.query.filter(EvaluationPoint.EPid == epid).first_("未找到该分数区间")
                if data.get("delete"):
                    ep_instance.update({"isdelete": 1})
                    msg = "删除成功"
                else:
                    ep_instance.update(ep_dict)
                    msg = "修改成功"
            db.session.add(ep_instance)
        return Success(message=msg)

    def list(self):
        """获取评测列表"""
        evaluation = Evaluation.query.filter(Evaluation.isdelete == 0).all_with_page()
        return Success(message="获取评测列表成功", data=evaluation)

    def get(self):
        """获取评测详情"""
        args = parameter_required(('token', 'evid', ))
        evid = args.get("evid")
        evaluation = Evaluation.query.filter(Evaluation.isdelete == 0, Evaluation.EVid == evid).first_("未找到该评测")
        evaluationitem = EvaluationItem.query.filter(EvaluationItem.isdelete == 0, EvaluationItem.EVid == evid)\
            .order_by(EvaluationItem.EIindex.asc()).all()
        for item in evaluationitem:
            eiid = item["EIid"]
            evaluationanswer = EvaluationAnswer.query.filter(EvaluationAnswer.isdelete == 0,
                                                             EvaluationAnswer.EIid == eiid)\
                .order_by(EvaluationAnswer.EAindex.asc()).all()
            item.fill("ea_list", evaluationanswer)
        evaluation.fill("ei_list", evaluationitem)
        user = token_to_user_(args.get('token'))
        if is_admin() or is_hign_level_admin():
            ep_list = EvaluationPoint.query.filter(EvaluationPoint.isdelete == 0)\
                .order_by(EvaluationPoint.EPstart.asc()).all()
            evaluation.fill("ep_list", ep_list)

        return Success(message="获取评测成功", data=evaluation)

    def make_evaluation(self):
        """提交评测"""
        data = parameter_required(('evid', 'ei_list'))
        if 'token' not in request.args.to_dict():
            return AuthorityError("请先登录")
        token = request.args.get('token')
        user = token_to_user_(token)
        usid = user.id
        evid = data.get('evid')
        anid = str(uuid.uuid1())
        with db.auto_commit():
            point = Decimal(0.0)
            evaluationitem_all = EvaluationItem.query.filter(EvaluationItem.isdelete == 0).all()
            if len(evaluationitem_all) != len(data.get('ei_list')):
                return EvaluationNumError()
            for ei in data.get('ei_list'):

                eiid = ei["eiid"]
                eaid = ei["eaid"]
                evaluationitem = EvaluationItem.query.filter(EvaluationItem.EIid == eiid,
                                                             EvaluationItem.isdelete == 0)\
                    .first_("未找到该题目")
                evaluationanswer = EvaluationAnswer.query.filter(EvaluationAnswer.EAid == eaid,
                                                                 EvaluationAnswer.isdelete == 0)\
                    .first_("未找到该选项")
                ai_dict = {
                    "AIid": str(uuid.uuid1()),
                    "EIname": evaluationitem["EIname"],
                    "EAindex": evaluationanswer["EAindex"],
                    "EApoint": evaluationanswer["EApoint"],
                    "EAname": evaluationanswer["EAname"],
                    "USid": usid,
                    "ANid": anid
                }
                point = Decimal(str(evaluationanswer["EApoint"] or 0)) + Decimal(str(point or 0))
                ai_instance = AnswerItem.create(ai_dict)
                db.session.add(ai_instance)
            evaluation = Evaluation.query.filter(Evaluation.isdelete == 0, Evaluation.EVid == evid).first_("未找到该评测")
            # 总积分逻辑改为平均分
            point = Decimal(str(point / len(evaluationitem_all)))
            evaluationpoint = EvaluationPoint.query.filter(EvaluationPoint.EPstart < point,
                                                           EvaluationPoint.EPend > point, EvaluationPoint.isdelete == 0)\
                .first_("未找到评测结论")
            answer = evaluationpoint["EPanswer"]
            an_dict = {
                "ANid": anid,
                "USid": usid,
                "EVid": evid,
                "EVname": evaluation["EVname"],
                "EPanswer": answer
            }
            an_instance = Answer.create(an_dict)
            db.session.add(an_instance)
        from .CConfig import CConfig
        from ..config.enums import PointTaskType
        CConfig()._judge_point(PointTaskType.make_evaluation.value, 1, usid)
        return Success(message="提交评测成功", data={"answer": answer})
