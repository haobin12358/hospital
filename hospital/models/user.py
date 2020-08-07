# -*- coding: utf-8 -*-
"""
用户相关信息：家人，地址等
create user: wiilz
last update time:2020/3/28 22:22
"""
from sqlalchemy import Integer, String, Text, Boolean, orm, DECIMAL
from hospital.extensions.base_model import Base, Column


class User(Base):
    """用户"""
    __tablename__ = "User"
    USid = Column(String(64), primary_key=True)
    USname = Column(String(255), nullable=False, comment='用户名')
    USavatar = Column(Text, url=True, comment='用户头像')
    USgender = Column(Integer, default=2, comment='性别 {0: unknown 1：male，2：female}')
    USlevel = Column(Integer, default=0, comment='vip等级')
    USintegral = Column(Integer, default=0, comment='用户积分')
    USbalance = Column(DECIMAL(precision=28, scale=2), default=0, comment='用户账户余额')
    USopenid = Column(Text, comment='小程序 openid')
    USunionid = Column(Text, comment='统一 unionID')
    UStelphone = Column(String(16), comment="手机号")
    UScardid = Column(String(32), comment="身份证号")

    @orm.reconstructor
    def __init__(self):
        super(User, self).__init__()
        self.hide('USopenid', 'USunionid')


class Family(Base):
    """家人"""
    __tablename__ = "Family"
    FAid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户ID')
    FArole = Column(Integer, default=3, comment='家人类型 1，本人 2，配偶 3，孩子')
    FAtype = Column(Integer, default=2, comment='1, 父亲 2，母亲 3，儿子 4，女儿')
    FAname = Column(String(255), comment='家人姓名')
    FAage = Column(Integer, default=1, comment='家人年龄')
    FAidentification = Column(String(18), comment='身份证号')
    FAtel = Column(String(13), comment='手机号')
    FAgender = Column(Integer, default=0, comment='性别 {0: unknown 1：male，2：female}')
    AAid = Column(String(64), comment='居住地区域ID')
    FAaddress = Column(Text, comment='家人居住地')
    FAself = Column(Boolean, default=False, comment='是否是本人')

    @orm.reconstructor
    def __init__(self):
        super(Family, self).__init__()
        self.hide('USid')


class UserAddress(Base):
    """用户地址"""
    __tablename__ = 'UserAddress'
    UAid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户id')
    UAname = Column(String(16), nullable=False, comment='收货人姓名')
    UAtel = Column(String(16), nullable=False, comment='收货人电话')
    UAtext = Column(String(255), nullable=False, comment='具体地址')
    UAdefault = Column(Boolean, default=False, comment='默认收货地址')
    AAid = Column(String(8), nullable=False, comment='关联的区域id')
    # UApostalcode = Column(String(8), comment='邮政编码')


class UserIntegral(Base):
    """用户积分表"""
    __tablename__ = 'UserIntegral'
    UIid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户id')
    UIintegral = Column(Integer, comment='该动作产生的积分变化数')
    UIaction = Column(Integer, default=1, comment='积分变动原因')
    UItype = Column(Integer, default=1, comment='积分变动类型 1 收入 2 支出 3 退还')
    UItrue = Column(Integer, default=0, comment='是否领取 0 未领取 1已领取')


class WalletRecord(Base):
    """余额变动记录"""
    __tablename__ = "WalletRecord"
    WRid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户id')
    WRcash = Column(DECIMAL(precision=28, scale=2), comment='变动金额')
    WRtype = Column(Integer, default=0, comment='1:充值 2:消费')
    ContentId = Column(String(128), comment='关联id, 充值时: OPayid， 消费时: OMid')


class IdentifyingCode(Base):
    """验证码"""
    __tablename__ = "IdentifyingCode"
    ICid = Column(String(64), primary_key=True)
    ICtelphone = Column(String(14), nullable=False)  # 获取验证码的手机号
    ICcode = Column(String(8), nullable=False)  # 获取到的验证码


class UserInvitation(Base):
    """用户邀请记录表"""
    __tablename__ = 'UserInvitation'
    UINid = Column(String(64), primary_key=True)
    USInviter = Column(String(64), comment='邀请人')
    USInvitee = Column(String(64), comment='被邀请人')
    UINapi = Column(String(100), comment='触发此次记录的api')


class UserHour(Base):
    """用户购买的课时"""
    __tablename__ = "UserHour"
    UHid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户ID')
    CLid = Column(String(64), comment='课程ID')
    SMnum = Column(Integer, default=0, comment='课时')
    UHnum = Column(Integer, default=0, comment='可用课时')
