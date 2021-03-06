# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text
from hospital.extensions.base_model import Base, Column


class Video(Base):
    """视频"""
    __tablename__ = 'Video'
    VIid = Column(String(64), primary_key=True)
    VImedia = Column(Text, url=True, comment='视频路由')
    VIname = Column(String(255), comment='视频名')
    VIthumbnail = Column(Text, url=True, comment='视频缩略图')
    SEid = Column(String(64), comment='系列ID')
    DOid = Column(String(64), comment='医生id')
    VIdur = Column(String(64), comment='时长')
    VIsort = Column(Integer, default=0, comment='排序')
    VIbriefIntroduction = Column(Text, comment='简介')


class Series(Base):
    """系列"""
    __tablename__ = 'Series'
    SEid = Column(String(64), primary_key=True)
    SEname = Column(String(255), comment='系列名')
    DOid = Column(String(64), comment='医生id')
    SEsort = Column(Integer, default=0, comment='排序')
