"""
本文件用于后台基本字段设置，包括但不限于关于我们/banner页等内容
create user: haobin12358
last update time:2020/3/12 15:39
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from hospital.extensions.base_model import Base, Column

class Banner(Base):
    """banner"""
    __tablename__ = 'Banner'
    BNid = Column(String(64), primary_key=True)
    ADid = Column(String(64), comment='创建者id')
    BNpicture = Column(Text, nullable=False, comment='图片', url=True)
    BNsort = Column(Integer, comment='顺序')
    contentlink = Column(LONGTEXT, comment='跳转链接')

class Setting(Base):
    """setting"""
    __tablename__ = "Setting"
    STid = Column(String(64), primary_key=True)
    STname = Column(String(128), nullable=False)
    STvalue = Column(LONGTEXT)
    STtype = Column(Integer, nullable=False, comment="{1:客服,2：关于我们}")

class Characteristicteam(Base):
    """特色团队"""
    __tablename__ = "Characteristicteam"
    CTid = Column(String(64), primary_key=True)
    CTpicture = Column(Text, nullable=False, comment='图片', url=True)
    CTname = Column(String(128), nullable=False, comment="姓名")
    CTposition = Column(String(128), nullable=False, comment='职位')
    CToffice = Column(String(128), nullable=False, comment='科室')

class Honour(Base):
    """医院荣誉"""
    __tablename__ = "Honour"
    HOid = Column(String(64), primary_key=True)
    HOpicture = Column(Text, nullable=False, comment="图片")
    HOtext = Column(Text, nullable=False, comment="文字")