# -*- coding: utf-8 -*-
"""
本文件用于处理评测相关数据库结构
create user: haobin12358
last update time:2020/3/29 05:06
"""
from sqlalchemy import Integer, String, Text, DECIMAL
from hospital.extensions.base_model import Base, Column


class Evaluation(Base):
    """
    问卷
    """
    __tablename__ = "Evaluation"
    EVid = Column(String(64), primary_key=True)
    EVname = Column(String(128), comment="问卷名称", nullable=False)
    EVpicture = Column(Text, url=True, comment="问卷图", nullable=False)


class EvaluationItem(Base):
    """
    问题
    """
    __tablename__ = "EvaluationItem"
    EIid = Column(String(64), primary_key=True)
    EIname = Column(String(128), comment="题目内容", nullable=False)
    EIindex = Column(Integer, comment="标号", nullable=False)
    EVid = Column(String(64), comment="问卷id", nullable=False)


class EvaluationAnswer(Base):
    """
    问题选项
    """
    __tablename__ = "EvaluationAnswer"
    EAid = Column(String(64), primary_key=True)
    EIid = Column(String(64), comment="问题id", nullable=False)
    EAindex = Column(String(8), comment="选项标号", nullable=False)
    EAname = Column(Text, comment="选项内容", nullable=False)
    EApoint = Column(DECIMAL(scale=2), comment="选项分值", nullable=False)


class EvaluationPoint(Base):
    """
    问卷分值区间对应结果
    """
    __tablename__ = "EvaluationPoint"
    EPid = Column(String(64), primary_key=True)
    EPstart = Column(DECIMAL(scale=2), comment="分值区间低", nullable=False)
    EPend = Column(DECIMAL(scale=2), comment="分值区间高", nullable=False)
    EVid = Column(String(64), comment="问卷id", nullable=False)
    EPanswer = Column(Text, comment="对应结论", nullable=False)
    EPtitle = Column(String(64), comment='分享图标题')
    EPanalysis = Column(String(64), comment='初步分析')
    EPevaluation = Column(Text, comment='评估建议')
    DOid = Column(String(64), comment='关联医生')
    DOname = Column(String(255), comment='医生名')
    EPaward = Column(String(64), comment='奖励语')
    EPshareWords = Column(Text, comment='分享语')
    EPshareLevel = Column(Integer, default=0, comment='0: 良好 1: 注意 2: 警惕')


class Answer(Base):
    """
    用户答案填写
    """
    __tablename__ = "Answer"
    ANid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment="用户id", nullable=False)
    EVid = Column(String(64), comment="问卷id", nullable=False)
    EVname = Column(String(128), comment="问卷名称", nullable=False)
    EVshare = Column(Text, url=True, comment='对应分享图')
    EPanswer = Column(Text, comment="对应结论")


class AnswerItem(Base):
    """
    用户答案填写项
    """
    __tablename__ = "AnswerItem"
    AIid = Column(String(64), primary_key=True)
    EIname = Column(String(128), comment="题目内容", nullable=False)
    EAindex = Column(String(8), comment="选项标号", nullable=False)
    EAname = Column(Text, comment="选项内容", nullable=False)
    EApoint = Column(DECIMAL(scale=2), comment="选项分值", nullable=False)
    USid = Column(String(64), comment="用户id", nullable=False)
    ANid = Column(String(64), comment="用户答案填写id", nullable=False)
