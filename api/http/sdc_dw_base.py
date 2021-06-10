#!/usr/bin/env python
# -*- coding:utf8 -*-


import traceback
from api.http.base_api import my_request
from api.http.hadoop_base_info import hdba
from utils import *


class SdcDwBasic:

    def __init__(self):
        self.hdba = hdba
        self.session = None  # 储存的session
        self.dbName_dicts = {1: [], 2: []}  # 本轮测试数据仓库的名字（1为主题，2为集市）
        self.referer = None  # 储存专有的referer值
        self.dbstat = None  # 仓库监控-搜索查询径                                                 /api/dw/monitor/dbstat
        self.design_dbs = None  # 仓库设计-搜索查询[get]                                          /api/dwdesign/dbManager/v1/dbs
        self.create_design_dbs = None  # 仓库设计-新建库[post]                                    /api/dwdesign/dbManager/v1/dbs
        self.delete_design_dbs = None  # 仓库设计-删除库[DELETE]                                  /api/dwdesign/dbManager/v1/dbs/{dbID}?dbName={dbName}
        self.run_dbs = None  # 仓库运行-查询已有库名                                               /api/dwrun/sqlParse/v1/dbs
        self.run = None  # 仓库运行-根据库名(dbName)执行sql语句                                     /api/dwrun/sqlParse/v1/{dbName}
        self.run_tbls = None  # 仓库运行-查询已有库 当中的表                                         /api/dwrun/sqlParse/v1/{dbname}/tbls
        self.run_records = None  # 仓库运行-根据库名(dbName)获取保存信息                             /api/dwrun/sqlParse/v1/{dbName}/records
        self.run_histories = None  # 仓库运行-根据库名(dbName)获取历史执行信息                        /api/dwrun/sqlParse/v1/{dbName}/histories
        self.run_objs = None  # 仓库运行-查询已有库 当中的存储过程或者函数                              /api/dwrun/sqlParse/v1/{dbName}/{obj_type}/objs
        self.run_conn = None  # 仓库运行-根据库名(dbName)获取连接关键字（connID）                     /api/dwrun/sqlParse/v1/conn
        self.run_conn_heart = None  # 仓库运行-根据库名(dbName) 监听 连接关键字（connID），是否运行正常  /api/dwrun/sqlParse/v1/conn/heart/{connid}
        self.get_interface_path()

    def get_interface_path(self):
        dw_config_path = get_config_path() + "\\globalconfig.ini"
        self.dbstat = read_config(dw_config_path, "dw", "dbstat_path")
        self.design_dbs = read_config(dw_config_path, "dw", "design_dbs_path")
        self.create_design_dbs = read_config(dw_config_path, "dw", "create_design_dbs_path")
        self.run_dbs = read_config(dw_config_path, "dw", "run_dbs_path")
        self.run_conn = read_config(dw_config_path, "dw", "run_conn_path")
        self.run_conn_heart = read_config(dw_config_path, "dw", "run_conn_heart_path")
        self.run = read_config(dw_config_path, "dw", "run_path")
        self.run_tbls = read_config(dw_config_path, "dw", "run_tbls_path")
        self.run_records = read_config(dw_config_path, "dw", "run_records_path")
        self.run_histories = read_config(dw_config_path, "dw", "run_histories_path")
        self.run_objs = read_config(dw_config_path, "dw", "run_objs_path")
        self.delete_design_dbs = read_config(dw_config_path, "dw", "delete_design_dbs_path")

    # 获取dw最新session对象及cookie
    def get_session_new(self):
        """
        判断 storage session 不为None，若为None，重新生成一个新的session
        :return:
        其他：#手动构建cookie
            https://blog.csdn.net/falseen/article/details/46962011
            https://blog.csdn.net/zhusongziye/article/details/80024586
        """
        try:

            if self.session is None or self.session != my_request.http_client_session:
                session_id = hdba.session_sdp_manage.cookies.get("ycyintang.session.id", path="/")
                # 构建加密的 fefere地址
                str_base64 = hdba.get_base64_enstr(hdba.url_sdc_dw.rstrip("/"))
                self.url_base64 = hdba.host_url + f"/proxy/{str_base64}/proxy/"
                # 构造依赖请求地址
                referer = '{}?sdpApi={}api/auth/checkLogin/{}'.format(self.url_base64, hdba.url_sdp_manage,
                                                                      session_id)
                self.referer = referer
                my_request.request('get', url=referer)
                self.session = my_request.http_client_session  # 替换最新session到http中
                hdba.session_sdp_manage.cookies.update(my_request.http_client_session.cookies)  # 更新session
            my_request.headers["Referer"] = self.referer
            return self.session
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 获取数据库的类型
    def get_dbType(self, dbType: int):
        """#获取数据库的类型
                Args:
                    int dbType: 类型：0为全部，1为主题，2为集市
                Returns:
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-27
                example：
                """
        dbType_name = ''
        if dbType == 0:
            dbType_name = '0-全部'
        elif dbType == 1:
            dbType_name = '1-主题'
        elif dbType == 2:
            dbType_name = '2-集市'
        else:
            dbType_name = None
        return dbType_name

    ###【1、仓库监控】
    # 仓库监控-搜索查询
    def dw_monitor_dbstat(self, data={'warehouseName': '', 'warehouseType': 0, 'pageSize': 9, 'pageNum': 1}):
        """#
                Args:
                    str warehouseName:  搜索关键字
                    int warehouseType: 类型：0为全部，1为主题，2为集市
                    int pageSize: 每页大小
                    int pageNum: 当前页

                Returns:
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-24
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()

            # url = hdba.host_url + "/api/dw/monitor/dbstat"
            url = hdba.host_url + self.dbstat
            # print(url)
            result = my_request.request('get', url=url, params=data)
            # print(result.response.text)
            data_dict = result.response.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    ###【2、仓库设计】
    # 仓库设计-搜索查询
    def dwdesign_dbManager_v1_dbs(self, data={'pageNum': 1, 'pageSize': 9, 'dbName': '', 'dbType': 0}):
        """#
                Args:
                    str dbName:  搜索数据库名字
                    int dbType: 类型：0为全部，1为主题，2为集市
                    int pageSize: 每页大小
                    int pageNum: 当前页

                Returns:
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-24
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwdesign/dbManager/v1/dbs"
            url = self.url_base64 + self.design_dbs
            result = my_request.request('get', url=url, params=data)
            data_dict = result.response.json()['data']
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库设计-新建库
    def creat_dwdesign_dbManager_v1_dbs(self, dbName, dbType, dbAlias='', dbDesc=''):
        """#
                Args:
                    str dbName: 仓库名称
                    int dbType: 类型：0为全部，1为主题，2为集市
                    str dbAlias: 显示名称
                    str pageNum: 数据仓库描述

                Returns:
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-24
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwdesign/dbManager/v1/dbs"
            url = self.url_base64 + self.create_design_dbs
            data = {"dbName": dbName,
                    "dbAlias": dbName if dbAlias == '' else dbAlias,
                    "dbType": dbType,
                    "dbDesc": self.get_dbType(dbType) + ':' + dbName if dbDesc == '' else self.get_dbType(
                        dbType) + ':' + dbAlias}
            result = my_request.request('post', url=url, json=data)
            # print(result.response.text)
            data_dict = result.response.json()
            # 创建库成功，把信息记录到
            if data_dict['success'] is True:
                self.dbName_dicts[dbType].append(dbName)
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    def delete_dwdesign_dbManager_v1_dbs(self, dbID, dbName):
        """#
                Args:
                    str dbName: 仓库名称
                    int dbType: 类型：0为全部，1为主题，2为集市
                    str dbAlias: 显示名称
                    str pageNum: 数据仓库描述
                Returns:
                Raises:
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwdesign/dbManager/v1/dbs/{dbID}?dbName={dbName}"
            url = self.url_base64 + eval(self.delete_design_dbs)
            result = my_request.request('delete', url=url)
            print(result.response.text)
            data_dict = result.response.json()
            # 删除成功，把信息记录到
            if data_dict['success'] is True:
                print(f"{dbName}删除成功")
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    ###【3、仓库运行】
    # 仓库运行-查询已有库名
    def dwrun_sqlParse_v1_dbs(self):
        """#
                Args:

                Returns: data_list 返回list
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-27
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/dbs"
            url = self.url_base64 + self.run_dbs
            result = my_request.request('get', url=url, headers=my_request.headers)
            data_list = result.response.json()['data']
            return data_list
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-查询已有库当中的 表
    def dwrun_sqlParse_v1_tbls(self, dbName, data={'key': '', 'pageNum': 1, 'pageSize': 100}):
        """#
                Args:

                Returns: data_list 返回list
                Raises:
                author： 袁鹏程（SF2533）
                createTime：2019-5-27
                example：
                """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/{}/tbls".format(dbName)
            url = self.url_base64 + eval(self.run_tbls)
            result = my_request.request('get', url=url, params=data)
            data_dict = result.response.json()
            assert data_dict['data'] is not None, "查询异常信息：{}".format(data_dict)
            data_list = data_dict['data']['list']
            return data_list
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e
            # log.error("【错误详细信息】：\n" + traceback.format_exc())

    # 仓库运行-查询已有库 当中的存储过程或者函数
    def dwrun_sqlParse_v1_objs(self, dbName, obj_type='func', data={'key': '', 'pageNum': 1, 'pageSize': 100}):
        """
        Args:
            str dbName：数据库名字
            str obj_type:返回对象类型 默认为 'func'，其参数范围为('func','proc')
        Returns: data_list 返回list
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            self.get_session_new()
            obj_types = ('func', 'proc')
            assert obj_type in obj_types, 'obj_type ({})值必须在obj_types中：{} '.format(obj_type, obj_types)
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/{}/{}/objs".format(dbName, obj_type)
            url = self.url_base64 + eval(self.run_objs)
            result = my_request.request('get', url=url, params=data)
            data_dict = result.response.json()
            assert data_dict['data'] != None, "查询异常信息：{}".format(data_dict)
            data_list = data_dict['data']['list']
            return data_list
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-根据库名(dbName)获取连接关键字（connID）
    def dwrun_sqlParse_v1_conn(self, dbName: str):
        """
        Args:
            str dbName:数据库名称
        Returns: data_str 返回字符串
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/conn"
            url = self.url_base64 + self.run_conn
            data = {"dbName": dbName}
            result = my_request.request('post', url=url, json=data)
            conn_id = result.response.json()['data']
            return conn_id
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-根据库名(dbName) 监听 连接关键字（connID），是否运行正常
    def dwrun_sqlParse_v1_conn_heart(self, conn_id: str):
        """
        Args:
            str dbName:数据库名称
        Returns: data_str 返回字符串
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/conn/heart/{}".format(conn_id)
            url = self.url_base64 + eval(self.run_conn_heart)
            result = my_request.request('get', url=url)
            # print(result.response.json())
            data_str = result.response.json()['success']
            if data_str == 'true':
                is_connect = True
            else:
                is_connect = False
            return is_connect
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-根据库名(dbName)获取保存信息
    def dwrun_sqlParse_v1_records(self, dbName: str, data={'pageNum': 1, 'pageSize': 10, 'key': ''}):
        """
        Args:
            str dbName:数据库名称
            dict data :{
            int pageNum :页号
            int pageSize：每页大小
            str key ：秘钥
            }
        Returns: data_str 返回字符串
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # https://10.0.6.58:17003/api/dwrun/sqlParse/v1/roc003/records?pageNum=1&pageSize=10&key=
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/{}/records".format(dbName)
            url = self.url_base64 + eval(self.run_records)
            result = my_request.request('get', url=url, params=data)
            data_str = result.response.json()['data']
            return data_str
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-根据库名(dbName)获取历史执行信息
    def dwrun_sqlParse_v1_histories(self, dbName: str, data={'pageNum': 1, 'pageSize': 10, 'key': ''}):
        """
        Args:
            str dbName:数据库名称
            dict data :{
            int pageNum :页号
            int pageSize：每页大小
            str key ：秘钥
            }
        Returns: data_str 返回字符串
        Raises:
        example：
        """
        try:
            # 0、获取最新 session
            self.get_session_new()
            # https://10.0.6.58:17003/api/dwrun/sqlParse/v1/roc003/records?pageNum=1&pageSize=10&key=
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/{}/histories".format(dbName)
            url = self.url_base64 + eval(self.run_histories)
            result = my_request.request('get', url=url, params=data)
            data_str = result.response.json()['data']
            return data_str
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e

    # 仓库运行-根据库名(dbName)执行sql语句
    def dwrun_sqlParse_v1(self, dbName: str, sql: str, connId: str, maxrows=200, is_assert=1):
        """
        Args:
            str dbName:数据库名称
            str sql:sql语句  （）
            str maxrows :最大返回行数
            int is_assert:是否进行断言检查 默认为1：进行检查，0不检查
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
            self.get_session_new()
            # https://10.0.6.58:17003/api/dwrun/sqlParse/v1/roc003/records?pageNum=1&pageSize=10&key=
            # url = self.url_base64 + "/api/dwrun/sqlParse/v1/{}".format(dbName)
            url = self.url_base64 + eval(self.run)
            data = {"content": sql,
                    "connId": connId,
                    "attr": {"maxrows": maxrows}}
            result = my_request.request('post', url=url, json=data)
            data_dict = result.response.json()['data']
            # 断言判断
            if data_dict['result'] != 0 and is_assert == 1:
                assert False, "执行sql异常,返回结果：\n{}".format(data_dict)
            return data_dict
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e


dw_basic = SdcDwBasic()

if __name__ == "__main__":
    from api.http.sdp_manage_base import manage_basic

    manage_basic.login_sdp_manage()
    data_dict = manage_basic.hdba.sdp_manage_api_user_session()
    print(data_dict)
    manage_basic.get_api_user_session()
    data_dict = dw_basic.dw_monitor_dbstat()
    print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_dbs()
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_tbls("beeline_jdbc")
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_objs("beeline_jdbc")
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_conn("beeline_jdbc")
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_conn_heart("beeline_jdbc")
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_records("beeline_jdbc")
    # print(data_dict)
    # data_dict = dw_basic.dwrun_sqlParse_v1_histories("beeline_jdbc")
    # print(data_dict)
    # connect_id = dw_basic.dwrun_sqlParse_v1_conn("beeline_jdbc")
    # data_dict = dw_basic.dwrun_sqlParse_v1_conn_heart(conn_id=connect_id)
    # print(data_dict)
