# -*- coding: utf-8 -*-
from ..extensions.base_enum import Enum


class TestEnum(Enum):
    ok = 66, '成功'


class TemplateEnum(Enum):
    msg = 0, 'f8o2hBAYwReg3wKq9PUG7X2jMHGW2xw17v1gXlrztWc'
    signin = 1, 'J7vtgP70BPwEuOiViQLRnb7w9AyZxbUzwFNNSG6lGxA'
    apply = 2, 'FXi_YKvy4C_bc5DGC9J0n3NROykpmQZCAXzBnKe5Bdc'
    order = 3, 'Nqqk5w_ZDq2UXdFa5M_0pjJ79HnpBn7YxO0wtQOMJew'
    finish = 4, 'gooKkXmSxBQC85KPXijwhmjjVRecy01wu59U1DZtl0U'


class ApplyTypeEnum(Enum):
    leaveApproval = 1, 'leaveApproval'
    overtimeApproval = 2, 'overtimeApproval'
    tripApproval = 3, 'tripApproval'
    cc = 4, 'tripApproval'

# if __name__ == '__main__':
