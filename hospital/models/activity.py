# -*- coding: utf-8 -*-
"""
医院活动部分
create user: wiilz
last update time:2020/3/30 15:15
"""
from sqlalchemy import Integer, String, Text, DateTime
from hospital.extensions.base_model import Base, Column


class Activity(Base):
    """活动"""
    __tablename__ = 'Activity'
    ACid = Column(String(64), primary_key=True)
    ADid = Column(String(64), comment='创建人id')
    ACname = Column(String(255), comment='活动名称')
    ACbanner = Column(Text, url=True, comment='活动主图')
    ACorganizer = Column(String(255), comment='举办人')
    ACstartTime = Column(DateTime, comment='活动时间')
    AClocation = Column(String(255), comment='活动地点')
    ACdetail = Column(Text, comment='活动介绍')
    ACnumber = Column(Integer, comment='活动人数')
    ACstatus = Column(Integer, default=0, comment='活动状态 0：未开始， 10：已结束')


class UserActivity(Base):
    """用户参加的活动"""
    __tablename__ = 'UserActivity'
    UAid = Column(String(64), primary_key=True)
    USid = Column(String(64))
    ACid = Column(String(64), comment='活动id')
    UAstatus = Column(Integer, default=0, comment='用户活动状态 0:待开始， 10：待评价， 20：已评价')
