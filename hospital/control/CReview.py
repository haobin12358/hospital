"""
本文件用于处理评论逻辑处理
create user: haobin12358
last update time:2020/4/2 1:50
"""
import uuid
import datetime
from decimal import Decimal
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_doctor, is_hign_level_admin, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.error_response import ParamsError, AuthorityError, StatusError
from hospital.models.departments import Doctor
from hospital.models.review import Review, ReviewPicture
from hospital.models.user import User
from hospital.models.classes import Course
from hospital.models.register import Register
from hospital.models.video import Video
from hospital.config.enums import ReviewStatus


class CReview:

    def get_review(self):
        """获取评论"""
        """案例404id/医生id/活动id403/视频id405/评价人名称==>rvtype+rvtypeid/usname/doid"""
        args = parameter_required(('token', ))
        user = token_to_user_(request.args.to_dict()["token"])
        if user.model == "Doctor":
            return AuthorityError()
        filter_args = [Review.isdelete == 0]
        if args.get('rvtype') and args.get('rvtypeid'):
            filter_args.append(Review.RVtypeid == args.get('rvtypeid'))
        if args.get('doid'):
            filter_args.append(Review.DOid == args.get('doid'))
        if args.get('usname'):
            filter_args.append(Review.USname.like("%{0}%".format(args.get('usname'))))
        review_list = Review.query.filter(*filter_args).order_by(Review.createtime.desc()).all_with_page()
        for review in review_list:
            if review["DOid"]:
                doctor = Doctor.query.filter(Doctor.DOid == review["DOid"], Doctor.isdelete == 0).first_("未找到医生信息")
                review.fill("doname", doctor["DOname"])
            rp = ReviewPicture.query.filter(ReviewPicture.RVid == review["RVid"], ReviewPicture.isdelete == 0).all()
            review.fill("createtime", review["createtime"])
            review.fill("rp_list", rp)
            rvtype = review["RVtype"]
            review.fill("rvtype_zn", ReviewStatus(rvtype).zh_value)

        return Success(message="获取评论成功", data=review_list)

    def set_review(self):
        """
        创建评论
        """
        data = parameter_required(("rvcontent", "rvtype", "rvtypeid", "rvnum"))
        user = token_to_user_(request.args.to_dict()["token"])
        usid = user.id
        rvtype = int(data.get('rvtype'))
        rvtypeid = data.get('rvtypeid')
        if rvtype == 401:
            """课程"""
            classes = Course.query.filter(Course.COid == rvtypeid).first_("未找到该课程排班")
            doid = classes["DOid"]
        elif rvtype == 402:
            """挂诊"""
            register = Register.query.filter(Register.REid == rvtypeid).first_("未找到该挂诊信息")
            doid = register["DOid"]
        elif rvtype == 403:
            """活动"""
            doid = None
        elif rvtype == 404:
            """案例"""
            doid = None
        elif rvtype == 405:
            """视频"""
            video = Video.query.filter(Video.VIid == rvtypeid).first_("未找到该视频信息")
            doid = video["DOid"]
        else:
            return StatusError("评论种类异常")
        rvid = str(uuid.uuid1())
        user_dict = User.query.filter(User.USid == usid).first_("未找到该用户")
        rv_dict = {
            "USid": usid,
            "USname": user_dict["USname"],
            "USavatar": user_dict["USavatar"],
            "RVcontent": data.get('rvcontent'),
            "DOid": doid,
            "RVtype": rvtype,
            "RVtypeid": data.get('rvtypeid'),
            "RVnum": Decimal(str(data.get('rvnum') or 0))
        }
        if data.get('rppicture_list'):
            rppicture_list = data.get('rppicture_list')
        else:
            rppicture_list = []
        with db.auto_commit():
            for repicture in rppicture_list:
                rp_dict = {
                    "RPid": str(uuid.uuid1()),
                    "RVid": rvid,
                    "RPpicture": repicture["rppicture"]
                }
                rv_instance = ReviewPicture.create(rp_dict)
                db.session.add(rv_instance)
            rv_dict["RVid"] = rvid
            rv_instance = Review.create(rv_dict)
            db.session.add(rv_instance)

        return Success("评论成功")

    def delete(self):
        """删除评论"""
        user = token_to_user_(request.args.to_dict()["token"])
        if user.model != "Admin":
            return AuthorityError()
        data = request.json
        with db.auto_commit():
            for rvid in data:
                rvid = rvid["rvid"]
                review_instance = Review.query.filter(Review.RVid == rvid).first_("未找到该评论")
                review_instance.update({"isdelete": 1})
                db.session.add(review_instance)
        return Success('删除成功')