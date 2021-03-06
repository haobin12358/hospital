# -*- coding: utf-8 -*-
from decimal import Decimal

from flask import current_app, request
import uuid

from hospital.extensions.interface.user_interface import is_user, admin_required, token_required, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, StatusError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Admin, Coupon, Products, Classes, Setting, Departments
from hospital.config.enums import ProductStatus, ProductType, AdminStatus, CouponStatus


class CProducts(object):

    # @token_required
    def list(self):
        data = parameter_required()
        filter_args = [Products.isdelete == 0, ]
        dename = data.get('dename')
        if dename:
            filter_args.append(Departments.DEname.ilike('%{}%'.format(dename)))
            filter_args.append(Departments.DEid == Products.DEid)
        if not is_admin():
            filter_args.append(Products.PRstatus == ProductStatus.usual.value)
        else:
            prtitle, prstatus, prtype = data.get('prtitle'), data.get('prstatus'), data.get('prtype')

            if prtitle:
                filter_args.append(Products.PRtitle.ilike('%{}%'.format(prtitle)))
            if prstatus:
                try:
                    prstatus = ProductStatus(int(str(prstatus))).value
                except:
                    raise ParamsError('商品状态异常')
                filter_args.append(Products.PRstatus == prstatus)
            if prtype:
                try:
                    prtype = ProductType(int(str(prtype))).value
                except:
                    raise ParamsError('商品类型筛选异常')
                filter_args.append(Products.PRtype == prtype)

        products = Products.query.filter(*filter_args).order_by(
            Products.PRsort.asc(), Products.createtime.desc()).all_with_page()
        for product in products:
            self._fill_coupon(product)
        return Success('获取成功', data=products)

    def get(self):
        data = parameter_required('prid')
        prid = data.get('prid')
        filter_args = [Products.PRid == prid, Products.isdelete == 0]
        if is_user():
            filter_args.append(Products.PRstatus == ProductStatus.usual.value)
        product = Products.query.filter(*filter_args).first_('商品已下架')
        product.add('PRdesc', 'PRdetails')
        self._fill_coupon(product)
        address = Setting.query.filter(Setting.STname == 'address', Setting.STtype == 2, Setting.isdelete == 0).first()
        telphone = Setting.query.filter(Setting.STname == 'telphone', Setting.STtype == 2, Setting.isdelete == 0).first()
        if address:
            product.fill('address', address.STvalue)
        else:
            product.fill('address', "")
        if telphone:
            product.fill('telphone', telphone.STvalue)
        else:
            product.fill('telphone', "")
        if product.DEid:
            dep = Departments.query.filter(Departments.DEid == product.DEid, Departments.isdelete == 0).first()
            if dep:
                product.fill('dename', dep.DEname)
            else:
                product.fill('dename', '')
        else:
            product.fill('dename', '')

        return Success('获取成功', data=product)

    @admin_required
    def add_or_update_product(self):
        data = parameter_required()
        # return
        # todo 修复
        adid = getattr(request, 'user').id
        admin = Admin.query.filter(Admin.ADid == adid, Admin.isdelete == 0,
                                   Admin.ADstatus == AdminStatus.normal.value).first_('当前管理员账号已冻结')

        prid, prprice, prvipprice, prtype, prstatus, printegral, prvipintegral, prstock, prsort, prdetails, smnum = (
            data.get('prid'), data.get('prprice'), data.get('prvipprice'), data.get('prtype'), data.get('prstatus'),
            data.get('printegral'), data.get('prvipintegral'), data.get('prstock'), data.get('prsort'),
            data.get('prdetails'), data.get('smnum'))
        deid = data.get('deid')
        if prprice:
            prprice = self._trans_decimal(prprice)
        if prvipprice:
            prvipprice = self._trans_decimal(prvipprice)
        if prtype:
            try:
                prtype = ProductType(int(prtype)).value
            except:
                raise ParamsError('商品类型参数异常')
            if prtype == ProductType.coupon.value and not data.get('coid'):
                raise ParamsError('缺少优惠券参数')
            if prtype == ProductType.package.value and not data.get('clid'):
                raise ParamsError('缺少课程参数')

        if prstatus:
            try:
                prstatus = ProductStatus(int(str(prstatus))).value
            except:
                raise ParamsError('商品状态参数异常')
        if data.get('coid') and prtype == ProductType.coupon.value:
            # 优惠券是否可用
            Coupon.query.filter(Coupon.COid == data.get('coid'), Coupon.COstatus == CouponStatus.use.value,
                                Coupon.isdelete == 0).first_('优惠券不可用')
        if data.get('clid') and prtype == ProductType.package.value:
            # 课程是否可用
            Classes.query.filter(Classes.CLid == data.get('clid'), Classes.isdelete == 0).first_('课程不存在')

        if printegral:
            printegral = self._check_int(printegral, '商品积分')
        if prvipintegral:
            prvipintegral = self._check_int(prvipintegral, '商品积分')
        if prstock:
            prstock = self._check_int(prstock, '商品库存')
        if prsort:
            prsort = self._check_int(prsort, '商品排序')
        if smnum:
            smnum = self._check_int(smnum, '课时数')
        if prdetails:
            if not isinstance(prdetails, list):
                raise ParamsError('prdetails 格式不对')
        if deid:
            Departments.query.filter(Departments.DEid == deid, Departments.isdelete == 0).first_('科室已删除')
        else:
            deid = ''

        with db.auto_commit():
            if prid:
                product = Products.query.filter(
                    Products.PRid == prid, Products.isdelete == 0).first()
                current_app.logger.info('get product {} '.format(product))
                # 优先判断删除
                if data.get('delete'):
                    if not product:
                        raise ParamsError('商品已删除')
                    current_app.logger.info('删除商品 {}'.format(prid))
                    product.isdelete = 1
                    db.session.add(product)
                    return Success('删除成功', data=prid)
                if product.PRstatus == ProductStatus.usual.value and prstatus == ProductStatus.usual.value:
                    raise StatusError('商品需要先下架才能修改')

                # 执行update
                if product:

                    update_dict = product.get_update_dict(data)
                    if prprice:
                        update_dict['PRprice'] = prprice
                    if prvipprice:
                        update_dict['PRvipPrice'] = prvipprice
                    if prtype:
                        update_dict['PRtype'] = prtype
                    if prstatus:
                        update_dict['PRstatus'] = prstatus
                    if printegral:
                        update_dict['PRintegral'] = printegral
                    if prvipintegral:
                        update_dict['PRvipIntegral'] = prvipintegral
                    if prstock:
                        update_dict['PRstock'] = prstock
                    if prsort:
                        update_dict['PRsort'] = prsort
                    if smnum:
                        update_dict['SMnum'] = smnum

                    update_dict['DEid'] = deid
                    product.update(update_dict)
                    current_app.logger.info('更新商品信息 {}'.format(prid))
                    db.session.add(product)
                    return Success('更新成功', data=prid)
            # 添加
            data = parameter_required({
                'prtitle': '商品名', 'prtype': '商品类型', 'prstock': '库存'
            })

            prid = str(uuid.uuid1())
            product = Products.create({
                'PRid': prid,
                'PRtitle': data.get('prtitle'),
                'PRtype': prtype,
                'PRmedia': data.get('prmedia'),
                'PRstatus': ProductStatus.auditing.value,
                'PRprice': prprice,
                'PRvipPrice': prvipprice,
                'PRintegral': printegral,
                'PRvipIntegral': prvipintegral,
                'PRstock': prstock,
                'COid': data.get('coid'),
                'CLid': data.get('clid'),
                'PRdetails': data.get('prdetails'),
                'PRdesc': data.get('prdesc'),
                'PRsort': prsort,
                'DEid': deid,
                'SMnum': smnum,
            })

            current_app.logger.info('{} 创建商品 {}'.format(admin.ADid, data.get('prtitle')))
            db.session.add(product)
        return Success('创建商品成功', data=prid)

    def _trans_decimal(self, price):
        if not price:
            return
        return Decimal(str(price))

    def _check_int(self, num, paramsname):
        if num is None:
            return
        try:
            trans_num = int(num)
            if trans_num < 0:
                raise ParamsError('{} 需要是正整数'.format(paramsname))
            return int(num)
        except:
            raise ParamsError('{}需要是整数'.format(paramsname))

    @admin_required
    def batch_operation(self):
        data = parameter_required('prstatus', )

        try:
            prstatus = ProductStatus(int(str(data.get('prstatus', 0)))).value
        except:
            raise ParamsError('状态参数异常')

        pridlist = data.get('pridlist', [])
        if not isinstance(pridlist, list):
            raise ParamsError('商品列表格式不对')
        with db.auto_commit():
            exec_sql = Products.query.filter(Products.PRid.in_(pridlist), Products.isdelete == 0)
            if prstatus == ProductStatus.delete.value:
                # 执行批量删除
                exec_sql.delete_(
                    synchronize_session=False)
                return Success('删除成功')
            exec_sql.update({'PRstatus': prstatus}, synchronize_session=False)

        return Success('{}成功'.format(ProductStatus(prstatus).zh_value))

    def _fill_coupon(self, product):
        if product.COid and product.PRtype == ProductType.coupon.value:
            coupon = Coupon.query.filter(Coupon.COid == product.COid, Coupon.isdelete == 0).first()
            if not coupon:
                return
            if coupon.COdownline == 0:
                coupon.fill("codownline_zh", "无限制")
            else:
                coupon.fill("codownline_zh", "满足{0}元即可使用".format(Decimal(str(coupon.COdownline))))
            coupon.fill("cotime", "{0}月{1}日-{2}月{3}日".format(
                coupon.COstarttime.month, coupon.COstarttime.day, coupon.COendtime.month, coupon.COendtime.day))
            product.fill('coupon', coupon)

        if product.CLid and product.PRtype == ProductType.package.value:
            classes = Classes.query.filter(Classes.CLid == product.CLid, Classes.isdelete == 0).first()
            if not classes:
                return
            product.fill('classes', classes)
