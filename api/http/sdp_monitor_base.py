#!/usr/bin/env python
# -*- coding:utf-8 -*-


import traceback
import sys
from api.http.base_api import my_request
from api.http.hadoop_base_info import hdba
import time
import re


class SdpMonitorBasic():

    def __init__(self):
        self.hdba = hdba
        self.session = None
        self.monitor_basic_url = None
        self.headers = my_request.get_default_headers()

        # str_time = str(time.time()*1000).split(".")[0]

    # comnn
    # 根据接口查询服务器的相关信息，返回一个字典数组混合体
    def get_service_component_name(self, data_dict={}):
        """#根据接口查询服务器的相关信息
                Args:data_dict 为get_ambari_service_component_info 返回的信息

                Returns:
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-7-15
                example：
                """
        if data_dict == {}:
            data_dict = self.get_ambari_service_component_info()
        service_component_dicts = {}
        for d in data_dict:
            service_name = d["ServiceComponentInfo"]["service_name"]  # 服务名 如hive
            if service_name not in service_component_dicts:
                service_component_dicts[service_name] = {}
            for host in d["host_components"]:
                host_components = host['HostRoles']  # 单个组件信息
                component_name = host_components['component_name']  # 组件名
                host_name = host_components["host_name"]  # 组件hostname
                if component_name not in service_component_dicts[service_name]:
                    service_component_dicts[service_name][component_name] = []
                service_component_dicts[service_name][component_name].append(host_name)
        return service_component_dicts

    # 获取sdp_monitor最新session对象及cookie
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
                session_id = hdba.session_sdp_manage.cookies.get("ycyintang.session.id", path="/").strip()
                # 构建加密的 rfeferer地址
                # host_port, url_suffix = hdba.get_host_url(hdba.url_sdp_monitor)
                # str_base64 = hdba.get_base64_enstr(host_port)
                # self.url_base64 = hdba.host_url + "/proxy/{}/proxy".format(str_base64)
                str_base64 = hdba.get_base64_enstr(hdba.url_sdc_dw.rstrip("/"))
                self.url_base64 = hdba.host_url + f"/proxy/{str_base64}/proxy/"

                # 构造依赖请求地址
                # referer = '{}/{}&sdpApi={}api/auth/checkLogin/{}'.format(self.url_base64, url_suffix,
                #                                                          hdba.url_sdp_manage,
                #                                                          session_id)
                referer = '{}?sdpApi={}api/auth/checkLogin/{}'.format(self.url_base64, hdba.url_sdp_manage,
                                                                      session_id)
                self.referer = referer
                print("referer 自连接url为：{}".format(referer))
                self.headers["Referer"] = self.referer
                new_url = self.url_base64 + "/api/v1/users/admin"
                authour = re.search("author=(.*)", url_suffix).group(1)
                self.headers["Authorization"] = "Basic {}".format(authour)
                self.headers["X-Requested-With"] = "XMLHttpRequest"
                result = my_request.request('get', url=new_url, headers=self.headers)
                # print(my_request.http_client_session.cookies)
                # print(result.response.cookies)
                # print(result.response.text)
                # my_request.http_client_session.cookies = result.response.cookies
                hdba.session_sdp_manage.cookies.update(my_request.http_client_session.cookies)  # 更新session
                self.session = my_request.http_client_session  # 替换最新session到http中
            my_request.headers["Referer"] = self.url_base64 + "/"
            return self.session
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 获取clusters 相关版本信息
    def api_v1_clusters_provisioning_state(self):
        """
        获取数据库的类型
        Args:

        Returns:
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            # log.info(self.session.cookies)
            self.get_session_new()
            str_time = str(time.time() * 1000).split(".")[0]
            url = self.url_base64 + "/api/v1/clusters?fields=Clusters/provisioning_state&_={}".format(str_time)
            result = my_request.request('get', url=url)
            data_dict = result.response.json()
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 获取clusters 相关版本信息（暂时未使用）
    def api_v1_clusters_provisioning_state1(self):
        """
        获取数据库的类型
        Args:
        Returns:
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            # log.info(self.session.cookies)
            self.get_session_new()
            str_time = str(time.time() * 1000).split(".")[0]
            url = self.url_base64 + "/api/v1/clusters/cluster/services?fields=ServiceInfo/state,ServiceInfo/maintenance_state,components/ServiceComponentInfo/component_name&minimal_response=true&_={}".format(
                str_time)
            result = my_request.request('get', url=url)
            data_dict = result.response.json()
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e
            # log.error("【错误详细信息】：\n" + traceback.format_exc())

    # 获取ambari 安装的各个组件想信息
    def get_ambari_service_component_info(self):
        """
        获取ambari 安装的各个组件想信息
        Args:
        Returns:
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            # log.info(self.session.cookies)
            self.get_session_new()
            str_time = str(time.time() * 1000).split(".")[0]
            url = self.url_base64 + "/api/v1/clusters/cluster/components/?fields=ServiceComponentInfo/service_name,ServiceComponentInfo/category,ServiceComponentInfo/installed_count,ServiceComponentInfo/started_count,ServiceComponentInfo/init_count,ServiceComponentInfo/install_failed_count,ServiceComponentInfo/unknown_count,ServiceComponentInfo/total_count,ServiceComponentInfo/display_name,host_components/HostRoles/host_name&minimal_response=true&_={}".format(
                str_time)
            result = my_request.request('get', url=url)
            # print(result.response.json())
            data_dict = result.response.json()["items"]
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 获取clusters 相关版本信息（暂时未使用）
    def api_v1_clusters_provisioning_state3(self):
        """
        获取数据库的类型
        Args:
        Returns:
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            # log.info(self.session.cookies)
            self.get_session_new()
            str_time = str(time.time() * 1000).split(".")[0]
            url = self.url_base64 + """/api/v1/clusters/cluster/components/?ServiceComponentInfo/component_name=APP_TIMELINE_SERVER|ServiceComponentInfo/component_name=JOURNALNODE|ServiceComponentInfo/component_name=ZKFC|ServiceComponentInfo/category=MASTER&fields=ServiceComponentInfo/service_name,host_components/HostRoles/display_name,host_components/
            HostRoles/host_name,host_components/HostRoles/state,host_components/HostRoles/maintenance_state,
            host_components/HostRoles/stale_configs,host_components/HostRoles/ha_state,host_components/HostRoles
            /desired_admin_state,&minimal_response=true&_={}""".format(str_time).strip("\n")
            result = my_request.request('get', url=url)
            data_dict = result.response.json()["items"]
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e


monitor_basic = SdpMonitorBasic()

if __name__ == "__main__":
    from api.http.sdp_manage_base import manage_basic
    manage_basic.login_sdp_manage()

    service_component_dicts = monitor_basic.get_service_component_name()
    hive2_server_ip = service_component_dicts["HIVE"]["HIVE_SERVER"]
    spark2_thrift_ip = service_component_dicts['SPARK2']['SPARK2_THRIFTSERVER']
    print(hive2_server_ip)
    print(spark2_thrift_ip)
