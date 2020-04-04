# -*- coding: utf-8 -*-
"""
公益援助部分
create user: wiilz
last update time:2020/3/28 00:20
"""
from sqlalchemy import Integer, String, Text, Date, orm
from hospital.extensions.base_model import Base, Column


class Assistance(Base):
    """公益援助申请"""
    __tablename__ = 'Assistance'
    ATid = Column(String(64), primary_key=True)
    USid = Column(String(64), nullable=False)
    ATname = Column(String(10), comment='被援助者姓名')
    ATbirthday = Column(Date, comment='出生年月')
    ATgender = Column(Integer, comment='性别')
    AThousehold = Column(String(255), comment='户籍地址')
    ATaddress = Column(String(255), comment='家庭地址')
    ATtelphone = Column(String(16), comment="手机号")
    ARids = Column(Text, comment='关联的亲属id : ["id1, "id2"]')
    ATcondition = Column(Text, comment='身体状况')
    ATtreatment = Column(Text, comment='治疗情况')
    AThospital = Column(String(100), comment='治疗医院')
    ATdetail = Column(Text, comment='申请项目细节')
    ATdate = Column(Date, comment='到院日期')
    ATincomeProof = Column(Text, comment='收入证明')
    ATstatus = Column(Integer, default=0, comment='审核状态，{-10: 未通过， 0: 待审核, 10: 已通过}')
    Reviewer = Column(String(64), comment='审核人id')
    RejectReason = Column(String(255), comment='拒绝原因')

    @orm.reconstructor
    def __init__(self):
        super(Assistance, self).__init__()
        self.hide('USid', 'ARids', 'Reviewer', 'RejectReason')


class AssistancePicture(Base):
    """证明图片"""
    __tablename__ = 'AssistancePicture'
    APid = Column(String(64), primary_key=True)
    ATid = Column(String(64))
    APtype = Column(Integer, comment='图片类型， 1：诊断证明 2：特困证明')
    APimg = Column(Text, url=True, comment='图片地址')


class AssistanceRelatives(Base):
    """援助对象亲属"""
    __tablename__ = 'AssistanceRelatives'
    ARid = Column(String(64), primary_key=True)
    USid = Column(String(64), nullable=False)
    ARtype = Column(Integer, comment='身份 1: 父亲 2：母亲')
    ARname = Column(String(20), comment='姓名')
    ARage = Column(Integer, comment='年龄')
    ARcompany = Column(String(100), comment='工作单位')
    ARsalary = Column(Integer, comment='月收入')

    @orm.reconstructor
    def __init__(self):
        super(AssistanceRelatives, self).__init__()
        self.hide('USid')
