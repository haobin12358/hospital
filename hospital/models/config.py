"""
本文件用于后台基本字段设置，包括但不限于关于我们/banner页等内容
create user: haobin12358
last update time:2020/3/16 1:50
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


class AddressProvince(Base):
    """省"""
    __tablename__ = 'AddressProvince'
    APid = Column(String(8), primary_key=True, comment='省id')
    APname = Column(String(20), nullable=False, comment='省名')


class AddressCity(Base):
    """市"""
    __tablename__ = 'AddressCity'
    ACid = Column(String(8), primary_key=True, comment='市id')
    ACname = Column(String(20), nullable=False, comment='市名')
    APid = Column(String(8), nullable=False, comment='省id')


class AddressArea(Base):
    """区县"""
    __tablename__ = 'AddressArea'
    AAid = Column(String(8), primary_key=True, comment='区县id')
    AAname = Column(String(32), nullable=False, comment='区县名')
    ACid = Column(String(8), nullable=False, comment='市名')

class PointTask(Base):
    """任务列表"""
    __tablename__ = "PointTask"
    PTid = Column(String(64), primary_key=True, comment="任务id")
    PTname = Column(String(255), comment="任务内容")
    PTtype = Column(Integer, comment="701登录702邀请新用户703完善个人信息704完善家人信息705购买会员"
                                     "706充值707看视频708挂号709评论710积分购物711报名活动712公益援助713健康测评")
    PTnumber = Column(Integer, comment="积分数")
    PTtime = Column(Integer, comment="限制次数， -表示限制次数+表示每日次数")
    PTicon = Column(Text, url=True, comment="icon")