#!/usr/bin/env python
# -*- coding:utf-8 -*-


import traceback
from typing import Dict
from api.http.base_api import my_request
from api.http.hadoop_base_info import hdba
from collections import namedtuple
import requests


class SdpManageBasic:

    def __init__(self):
        self.session = None  # session
        self.username = None  # 当前登录用户
        self.hdba = hdba  # hadoop 基础信息

    def switch_session(self):
        """
        #切换session
        :return:
        """
        assert self.session is None, "SdpManageBasic https session is not None"
        my_request.http_client_session = self.session

    def login_sdp_manage(self, username="admin"):
        """
        调用登录接口，获取用户权限列表
        :return
        """
        try:
            login_info = hdba.get_login_userinfo()  # 登录信息
            print(login_info)
            basc_url = login_info["url_sdp_manage"]
            name = login_info["name"]
            pwd = login_info["pwd"]
            data = {
                "code": "dslw",
                "userName": name,
                "pwd": pwd
            }
            url = basc_url + "api/user/login"
            my_request.http_client_session = my_request.requests.session()
            result = my_request.request('post', url=url, json=data, verify=False)
            data_dict = result.response.json()['data']
            roleId = data_dict['roleId']
            # 发起新的请求：
            my_request.headers["Referer"] = basc_url
            url = hdba.host_url + "/sdp_manage/api/role/queryRoleById?roleId={}".format(roleId.strip())
            result = my_request.request('get', url=url, verify=False)
            my_request.http_client_session.cookies = result.response.cookies  # 替换session
            data_dict_role = result.response.json()['data']

            self.session = my_request.http_client_session  # 更换session
            hdba.session_sdp_manage = my_request.http_client_session  # 转储存session

            # 获取登录后的 相关菜单地址
            menu_tuple = self.get_menu_ist(data_dict)
            # print(menu_tuple)
            hdba.url_sdc_etl = menu_tuple.sdc_etl.permissionUrl  # 数据融合
            hdba.url_sdc_storage = menu_tuple.sdc_storage.permissionUrl  # 数据存储
            sdc_dw_menu_tuple = self.get_menu_ist(menu_tuple.sdc_dw.children)  # 获取仓库二级菜单
            hdba.url_sdc_dw = sdc_dw_menu_tuple.sdc_dw.permissionUrl  # 仓库管理系统
            hdba.url_sdc_dw_sql = sdc_dw_menu_tuple.sdc_sql.permissionUrl  # 多维分析
            hdba.url_sdc_search = menu_tuple.sdc_search.permissionUrl  # 数据检索
            hdba.url_sdc_security = menu_tuple.sdc_security.permissionUrl  # 数据安全
            install_operation_tuple = self.get_menu_ist(menu_tuple.install_operation.children)
            hdba.url_sdc_install = install_operation_tuple.sdc_install.permissionUrl  # 安装部署
            hdba.url_sdp_monitor = install_operation_tuple.sdp_monitor.permissionUrl  # 运维监控
            hdba.url_sdc_shell = install_operation_tuple.sdc_shell.permissionUrl  # 命令解析
            hdba.url_sdc_log = install_operation_tuple.sdc_log.permissionUrl  # 日志记录
            # 存到一个字典中好查看数据
            hdba.urls['sdc_etl'] = hdba.url_sdc_etl
            hdba.urls['sdc_storage'] = hdba.url_sdc_storage
            hdba.urls['sdc_dw'] = hdba.url_sdc_dw
            hdba.urls['sdc_sql'] = hdba.url_sdc_dw_sql
            hdba.urls['sdc_search'] = hdba.url_sdc_search
            hdba.urls['sdc_security'] = hdba.url_sdc_security
            hdba.urls['sdp_monitor'] = hdba.url_sdp_monitor
            hdba.urls['sdc_shell'] = hdba.url_sdc_shell
            hdba.urls['sdc_log'] = hdba.url_sdc_log
            hdba.urls['sdc_install'] = hdba.url_sdc_install
            # 返回值
            # print(hdba.urls)
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    def get_menu_ist(self, data_dict: dict):
        """
        接口登录后获取各个菜单的链接地址：
        Args:
            dict menuList: 菜单列表（参数为login_sdp_manage()或get_api_user_session()的返回值）
            或者处理 children下的子菜单（传入一个参数list），再次调用该方法
        Returns: 一个 menu_tuple 对象
        一级属性：['sdc_etl', 'sdc_storage', 'sdc_dw', 'sdc_search', 'sdc_security', 'sdc_snake'，install_operation]
        二级属性：['permissionName', 'title', 'permissionUrl', 'permissionUrlByHttps', 'route', 'install', 'softname', 'children']
        三级属性：需要二次调用，并传入一个list
        Raises:
        example：
        """
        try:
            if "menuList" in data_dict:
                menu_list = data_dict['menuList']
                menu_layer = ""
            else:
                menu_list = list(data_dict)  # 传一个参数list
                menu_layer = "children"

            def menu_list_deal(name: str, li_dict: dict):
                """
                处理list 中的字典 li_dict
                二级属性：['permissionName', 'title', 'permissionUrl', 'permissionUrlByHttps',
                'route', 'install', 'softname', 'children']
                :param li_dict:
                :return:
                """
                # 创建一个名字
                global menu_name
                if name == "softname":
                    menu_name = li_dict[name].split(',')[0]
                elif name == "route":
                    menu_name = li_dict[name].split('/')[-1]

                softname = namedtuple(menu_name.capitalize(), li_dict.keys())._make(li_dict.values())
                return softname

            # 封装成一个新的字典对象
            menu_list_dict = {}
            for li_dict in menu_list:
                if "softname" in li_dict:
                    name = 'softname'
                elif "softNames" in li_dict:
                    name = 'route'
                else:
                    name = 'softname'
                if li_dict[name] is None and li_dict['children'] != []:
                    title = li_dict['title']
                    if title == "安装运维":
                        li_dict[name] = 'install_operation'
                if li_dict[name] is not None and len(li_dict[name]) > 1:
                    if name == "route":
                        menu_name = li_dict[name].split('/')[-1]
                    else:
                        menu_name = li_dict[name].split(',')[0]

                    menu_list_dict[menu_name] = menu_list_deal(name, li_dict)
            # print(menu_list_dict)
            Menu = namedtuple("Menu", menu_list_dict.keys())
            menu_tuple = Menu._make(menu_list_dict.values())
            return menu_tuple
        except Exception as e:
            raise e

    def get_api_user_session(self, force_login=1) -> Dict:
        """
        检查session
        Args:
            str username: 登录用户名
            int force_login:  1为强制登录(默认强制)，0位不登录
        Returns:
        Raises:
        example：
        """
        try:
            url = hdba.url_sdp_manage + "api/user/session"
            print("获取session的url地址为:")
            print(url)
            my_request.headers["Referer"] = hdba.url_sdp_manage
            result = my_request.request('get', url=url)
            data_dict = result.response.json()
            if data_dict['code'] == 1 and force_login == 1:
                username = self.username if self.username is not None else 'user_name_admin'
                data_dict = self.login_sdp_manage(username=username)
                print("登录信息为:")
                print(data_dict)
                return data_dict
            else:
                return data_dict['data']
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    def get_api_auth_checkLogin(self):
        """
        接口登录sdp_manage
        Args:
        Returns:
        Raises:
        example：
        """
        try:
            url = hdba.host_url + "/api/auth/checkLogin"
            result = my_request.my_requests('get', url=url)
            data_dict = result.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())


manage_basic = SdpManageBasic()
if __name__ == "__main__":
    # print("manage_basic.hdba.headers is")
    # print(my_request.headers)
    # print(manage_basic.hdba.headers)
    manage_basic.login_sdp_manage()
    # data_dict = manage_basic.get_api_user_session()
    # print(data_dict)
    # data_dict = manage_basic.get_api_auth_checkLogin()
    # print(data_dict)
