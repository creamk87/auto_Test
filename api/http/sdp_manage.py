#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author:YuanPengcheng
@createtime:2019/5/23 20:33
@software: PyCharm
@description: hadoop 管理页面
"""

import traceback
from api.http.sdp_manage_base import manage_basic
from api.http.sdp_install_base import install_basic
from api.http.sdp_monitor_base import monitor_basic


class SdpManage:

    def __init__(self):
        self.manage_basic = manage_basic
        self.install_basic = install_basic
        self.monitor_basic = monitor_basic

    # 检查 用户是否登录
    def check_sdp_manage_login(self, username='admin'):
        # 检查用户是否登录状态
        data_dict = self.manage_basic.hdba.sdp_manage_api_user_session()  # 此处不需要强制登录
        if data_dict is None:
            print("准备开始登录：")
            manage_basic.login_sdp_manage(username=username)


sdp_manage = SdpManage()
if __name__ == "__main__":
    sdp_manage.check_sdp_manage_login()
