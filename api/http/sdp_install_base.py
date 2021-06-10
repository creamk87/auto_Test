#!/usr/bin/env python
# -*- coding:utf-8 -*-

import traceback
from api.http.base_api import my_request
from api.http.hadoop_base_info import hdba


class SdcInstallBasic():

    def __init__(self):
        self.hdba = hdba
        self.session = None  # 储存的session
        self.referer = None  # 储存专有的referer值
        self.hosts_info = None  # 默认获取相关hosts 信息

    # my common
    # 处理服务器host相关信息
    def get_hosts_info(self, data_dict={}):
        """
        data_dict: 通过下面接口返回的信息
        data_dict=install_basic.api_deploy_rackQuery()
        判断 install session 不为None，若为None，重新生成一个新的session
        :return:
        返回所有的host信息

        """
        if data_dict == {}:
            data_dict = self.api_deploy_rackQuery()
        hosts_info = {}
        rack_list_info = data_dict['result']  # 机架数组
        for rack in rack_list_info:  #
            serverInfoResp_list = rack["serverInfoResp"]  # 机架上的服务信息
            for server in serverInfoResp_list:  # 域名
                hostName = server["hostName"]
                hostIp = server['hostIp']  # ip
                nodeRole = server['nodeRole']  # 角色
                host_info = [hostName, hostIp, nodeRole]
                hosts_info[hostName] = host_info
                # print(server)

        self.hosts_info = hosts_info
        print("当前机架信息为：\n{}".format(hosts_info))
        return hosts_info

    # 获取dw最新session对象及cookie
    def get_session_new(self):
        """
        判断 install session 不为None，若为None，重新生成一个新的session
        :return:
        其他：#手动构建cookie
            https://blog.csdn.net/falseen/article/details/46962011
            https://blog.csdn.net/zhusongziye/article/details/80024586
        """
        try:

            if self.session is None or self.session != my_request.http_client_session:
                # print(hdba.session_sdp_manage.cookies.get("ycyintang.session.id", path="/sdp_manage"))
                session_id = hdba.session_sdp_manage.cookies.get("ycyintang.session.id", path="/sdp_manage").strip()
                # 构建加密的 Referer地址
                # host_port, url_suffix = hdba.get_host_url(hdba.url_sdc_install)
                # # http://sdc213.sefon.com:18094   /sdc_install/
                # print(host_port, url_suffix)
                # str_base64 = hdba.get_base64_enstr(host_port)
                # # self.url_base64 = hdba.url_sdp_manage + "/proxy/{}/proxy/{}".format(str_base64, url_suffix)
                # self.url_base64 = hdba.host_url + "/proxy/{}/proxy/{}".format(str_base64, url_suffix)
                str_base64 = hdba.get_base64_enstr(hdba.url_sdc_dw.rstrip("/"))
                self.url_base64 = hdba.host_url + f"/proxy/{str_base64}/proxy/"
                # 构造依赖请求地址
                referer = '{}?sdpApi={}api/auth/checkLogin/{}'.format(self.url_base64, hdba.url_sdp_manage,
                                                                      session_id)
                self.referer = referer
                result = my_request.request('get', url=referer)
                self.session = my_request.http_client_session  # 替换最新session到http中
                hdba.session_sdp_manage.cookies.update(my_request.http_client_session.cookies)  # 更新session
            my_request.headers["Referer"] = self.referer
            # print("self.session is")
            # print(self.session.cookies)
            return self.session
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 安装部署-获取机房信息
    def api_deploy_roomQuery(self, pageNum=1, pageSize=100):
        """
        Args:
            int pageNum:页数
            int pageSize:每页大小
        Returns:
          {"result":0,"msg":"OK","detilMsg":null,"
          duration":10.13,
          "head":["NO","NAME","LOC"],
          "data":[],"affectNum":0},"success":true,"error":null
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            cookies = self.get_session_new().cookies
            # https://10.0.6.58:17003/api/dwrun/sqlParse/v1/roc003/records?pageNum=1&pageSize=10&key=
            url = self.url_base64 + "/api/deploy/roomQuery"
            # print(url)
            data = {"pageNum": pageNum,
                    "pageSize": pageSize}
            result = my_request.my_requests('post', url=url, json=data, cookies=cookies)
            data_dict = result.response.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 安装部署-获取某个机房下的 服务器信息
    def api_deploy_rackQuery(self, roomId=1, pageNum=1, pageSize=255):
        """
        Args:
            int roomId :机房id
            int pageNum:页数
            int pageSize:每页大小

        Returns:
          {"result":0,"msg":"OK","detilMsg":null,"
          duration":10.13,
          "head":["NO","NAME","LOC"],
          "data":[],"affectNum":0},"success":true,"error":null
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            cookies = self.get_session_new().cookies
            # http://10.0.8.213:21000/sdc_install/api/deploy/rackQuery
            url = self.url_base64 + "api/deploy/rackQuery"
            # print(self.url_base64)
            # print(url)
            data = {"roomId": roomId,
                    "pageNum": pageNum,
                    "pageSize": pageSize}
            result = my_request.request('post', url=url, json=data, cookies=cookies)
            # print(result.text)
            data_dict = result.response.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e


install_basic = SdcInstallBasic()

if __name__ == "__main__":
    from api.http.sdp_manage_base import manage_basic
    data_dict = manage_basic.login_sdp_manage()
    install_basic.get_hosts_info()
