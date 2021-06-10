#!/usr/bin/env python
# -*- coding:utf-8 -*-
import base64
import re
import traceback
from collections import namedtuple
from api.http.base_api import my_request
from utils import *


class HadoopRequestsBasic:

    def __init__(self):
        self.session_sdp_manage = None  # 记录sdp_manage 的session
        self.url_sdp_manage = None  # hadoop 主要登录url(需要初始化方法get_login_info)，globalconfig.ini 中进行配置
        self.urls = {}  # 记录所有的urls地址
        self.create_url = None
        self.cookies = None
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.encrypt_password = None
        self.host_url = None  # http://10.0.8.213:21000
        self.basic_url = None  #
        self.login_url = None  # http://10.0.8.213:21000/proxy/aHR0cDovLzEwLjAuOC4yMTM6MTgwODA=/proxy/sdp_manage/api/user/login
        self.query_url = None  # http://10.0.8.213:21000/proxy/aHR0cDovLzEwLjAuOC4yMTM6MTgwODA=/proxy/sdp_manage/api/role/queryRoleById?roleId=
        self.verify = False  # 默认设置是否需要进证书校验,默认不需要（主要https用）
        self.get_login_userinfo()  # 初始化时登录系统，获取相关url地址链接
        # 默认相关地址(登录后获取)
        self.url_sdc_etl = None  # 数据融合
        self.url_sdc_storage = None  # 数据存储
        self.url_sdc_dw = None  # 仓库管理系统
        self.url_sdc_dw_sql = None  # 多维分析
        self.url_sdc_search = None  # 数据检索
        self.url_sdc_security = None  # 数据安全
        self.url_sdc_install = None  # 安装部署
        self.url_sdp_monitor = None  # 运维监控 sdc_console
        self.url_sdc_shell = None  # 命令解析
        self.url_sdc_log = None  # 日志记录
        self.hadoop_config_path = get_config_path() + "\\globalconfig.ini"

        self.headers = my_request.get_default_headers(content_type=0)
        my_request.headers = self.headers

    def get_login_userinfo(self) -> Dict:
        """
        从配置文件中获取登录的用户名、密码、并赋值给初始化对象
        :return: None
        """
        user_info_path = get_config_path() + "\\globalconfig.ini"
        self.url_sdp_manage = read_config(user_info_path, "hadoop", "url").strip()
        self.username = read_config(user_info_path, "hadoop", "user_name").strip()
        self.encrypt_password = read_config(user_info_path, "hadoop", "encrypt_password")
        self.host_url = re.search('^https*://\d+\.\d+\.\d+\.\d+:\d+', self.url_sdp_manage)[0]
        self.basic_url = self.url_sdp_manage.rstrip("/").rstrip("sdp_manage").rstrip("/")
        result = {
            "url_sdp_manage": self.url_sdp_manage,
            "name": self.username,
            "pwd": self.encrypt_password
        }
        print(f"接口登录信息为：{result}")
        return result

    def get_dw_info(self):
        """
        :function:根据配置获取hadoop相关数仓dw相关信息
        :param username:
        :return:
        """
        test_onOff = read_config(self.hadoop_config_path, "dw", "test_onOff")
        # print("数仓test_onOff:" + str(test_onOff))
        return test_onOff

    def get_menu_ist(self, data_dict: Dict):
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
                # print(li_dict['children'])
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

    def get_base64_enstr(self, enstr):
        """
        #反编译
        # s = "aHR0cDovLzEwLjAuNi41NzoxNzAwMQ=="
        # b1 = bytes(s.encode("utf-8"))
        :param url:
        :return:
        """
        encodestr = base64.b64encode(enstr.encode('utf-8'))
        value = str(encodestr, 'utf-8')
        return value

    def sdp_manage_api_user_session(self):
        """
        检查session
        Args:
            str username: 登录用户名
        Returns:
        Raises:
        example：
        """
        try:
            url = hdba.url_sdp_manage + "api/user/session"
            # print(hdba.url_sdp_manage)
            if "Referer" in my_request.headers.keys():
                my_request.headers.pop("Referer")
            result = my_request.request('get', url=url)
            data_dict = result.response.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    def get_host_url(self, url):
        """
        #获取一个网址带https的ip和端口
        :param url:
        :return:
        """
        host_port = re.search("(https*://.*:\d+)/", url).group(1)
        url_suffix = url.split(host_port)[-1]
        print("获取带http的ip：{}，返回值host_port：{},url_suffix:{}".format(url, host_port, url_suffix))
        return host_port, url_suffix

    def except_deal(self, e, traceback):
        """
        #处理接口异常信息
        :param e:   捕获到的异常类
        :param traceback:  异常相关信息
        :return: 异常类型
        """
        except_type = type(e)
        print(f"抛出异常类型为：{except_type}，异常信息为：{traceback}")
        return except_type

hdba = HadoopRequestsBasic()
if __name__ == "__main__":
    hdba = HadoopRequestsBasic()
    a = hdba.get_login_userinfo()
    print(a)
