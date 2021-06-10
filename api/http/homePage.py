#!/usr/bin/env python
# -*- coding:utf-8 -*-


from api.http.sdc_dw import sdc_dw
from api.http.sdp_manage import sdp_manage
from api.http.sdp_monitor_base import monitor_basic


class HomePage:
    def __init__(self):
        self.sdc_dw = sdc_dw
        self.sdp_manage = sdp_manage
        self.monitor_basic = monitor_basic
        # self.sh_order = sh_order  # hive 后台


hp = HomePage()

if __name__ == "__main__":
    # hp.sdp_manage.check_sdp_manage_login()
    hp.sdp_manage.check_sdp_manage_login()
