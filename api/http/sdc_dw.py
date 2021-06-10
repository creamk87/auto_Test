#!/usr/bin/env python
# -*- coding:utf-8 -*-


import traceback
import sys
from .sdc_dw_base import dw_basic
from collections import defaultdict
from utils import *
import re
import time


class SdcDw:

    def __init__(self):
        self.dw_basic = dw_basic
        self.dbName_dict = {1: ["autoTest_roc"], 2: []}  # 本轮测试数据仓库的名字（1为主题，2为集市）
        # self.dbName_dict = {1: [], 2: []}  # 本轮测试数据仓库的名字（1为主题，2为集市）
        self.conn_id_dict = defaultdict(list)  # 根据库名为key,conn_id_list为value值
        self.conn_id_sqltype_dict = defaultdict(str)  # 根据 conn_id 记录其sqltype
        self.default_sqltype = 'plsql'  # 默认设置 set session sqltype=plsql;
        self.test_onOff = dw_basic.hdba.get_dw_info()

    # 获取sql配置文件信息
    def get_sql_path_info(self, table_name, sqltype='plsql'):
        """
        str table_name:  dwrun_plsql.ini 中的section
        :return:
        """
        if sqltype == "plsql":
            pass
            # path = read_config(initialize_file_path, "hadoop", "") + "dwrun_plsql.ini"
        elif sqltype == "sqlserver":
            path = dw_basic.hdba.hadoop_config_path + "dwrun_sqlserver.ini"
        else:
            path = dw_basic.hdba.hadoop_config_path + "dwrun_plsql.ini"

        # sections = appRoot.get_sections(path)
        # assert table_name in sections, "表名({})的【sections】不在配置文件{}中".format(table_name, path)
        # log.info("sections:{}".format(sections))
        # table_info_dict = appRoot.read_config_dict(path, section=table_name)
        # return table_info_dict

    def set_session_sqltype(self, dbName, connId, sqltype):
        """
        设置session sqltype,根据传入的sqltype类型，执行sql语句
        """
        if sqltype == "plsql":
            sql = "set session sqltype=PLSQL;"
            data_dict = self.dw_basic.dwrun_sqlParse_v1(dbName=dbName, sql=sql, connId=connId)
            assert data_dict["msg"] == "OK", f"set session sqltype=PLSQL执行失败\n 返回结果data_dict:\n{data_dict['data']}"
        elif sqltype == "sqlserver":
            sql = "set session sqltype=sqlserver;"
            data_dict = self.dw_basic.dwrun_sqlParse_v1(dbName=dbName, sql=sql, connId=connId)
            assert data_dict["msg"] == "OK", f"set session sqltype=sqlserver执行失败\n 返回结果data_dict:\n{data_dict['data']}"

    # 初始化plsql数据库
    def initialize_tables_plsql(self, db_name: str, initialize_sql: Dict):
        """
        初始化plsql数据库
        db_name: 传入要初始化的数据库名
        initialize_sql: 初始化的sql语句，json数据，从yml文件获取 “00Hadoop_initialize_database.yml”
        """
        # 获取初始化表的sql语句列表
        tb_insert_person_info: List = initialize_sql["insert_person_info"]
        tb_emp: List = initialize_sql["emp"]
        tb_dept: List = initialize_sql["dept"]
        # 获取数据库连接id
        conn_id = self.get_dbName_connId(db_name=db_name)

        def dwrun_sql(dbName, sql_list):
            """
            执行传入List中的sql语句
            """
            for sql in sql_list:
                # 每句sql执行前，执行set session操作
                self.set_session_sqltype(dbName=dbName, connId=conn_id, sqltype="plsql")
                self.dw_basic.dwrun_sqlParse_v1(dbName=dbName, sql=sql, connId=conn_id)

        # 挨个调用dwrun_sql方法，执行列表中的sql语句
        dwrun_sql(dbName=db_name, sql_list=tb_insert_person_info)
        dwrun_sql(dbName=db_name, sql_list=tb_emp)
        dwrun_sql(dbName=db_name, sql_list=tb_dept)

    # 设置 conn_id 的sqltype  set session sqltype=sqlserver 和plsql;
    def set_connid_session_sqltype(self, db_name, conn_id, sqltype=None):
        """
        str db_name:  数据库名字
        str conn_id: 数据库连接的关键字
        str sqltype: 当前sqltyp  set session sqltype=sqlserver;
        :return:
        """
        try:
            # 调用sql语句执行
            sql = f"set session sqltype ={sqltype};"
            data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql=sql, connId=conn_id)
            assert data_dict["result"] == 0, f'{db_name}库设置conn_id {conn_id}失败，其信息为：\n{data_dict}'
            self.conn_id_sqltype_dict[conn_id] = sqltype.lower()
            print(f"已经set session {sqltype} 设置con_id 的sqltype 汇总为：\n{self.conn_id_sqltype_dict}")
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 新建一个 数据库名字（仅仅是名字）
    def get_dbName_new(self, basic_name='autoTest_'):
        """
        str basic_name:  新创建数据库名字的前缀
        :return:
        """
        try:
            dbName = basic_name + get_timestamp()
            return dbName
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 根据不同的数据库类型，创建并返回其数据库名字
    def get_dbName_save(self, dbType, db_name=None, is_save=1, force_new=0):
        """
        int dbType : 1为主题库，2为集市库
        str db_name:  指定 库的名字
        int is_save: 0为不保存，1为保存   （保存到当前类）
        :return: db_name
        """
        try:
            # 1、判断当前实例的dbName 是否为None
            if db_name is None:
                if self.dbName_dict[dbType] is not []:
                    db_name = self.dbName_dict[dbType][0]  # 默认取第一个值
                else:
                    # 2、需要创建一个新库
                    db_name = self.get_dbName_new()
            # 检查当前库是否存在，若不存在创建该库
            db_list = dw_basic.dwrun_sqlParse_v1_dbs()
            if db_name not in db_list:
                dw_basic.creat_dwdesign_dbManager_v1_dbs(db_name, dbType)
                # 新创建的库 是否强制保存
                if is_save == 1 and db_name not in self.dbName_dict[dbType]:
                    self.dbName_dict[dbType].append(db_name)
            print(f"使用的库为db_name：{db_name}")
            return db_name
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 根据不同的数据库，从self.conn_id_dict 返回它的链接connId
    def get_dbName_connId(self, db_name, is_new=0, sqltype='plsql'):
        """
        str db_name : 数据库名称
        int is_new:是否新生成一个，0不生成，1为强制生成
        :return: conn_id
        """
        sqltype_list = ['plsql', 'sqlserver']
        assert sqltype in sqltype_list, "输入参数sqltype：{} 错误，正确参数范围为：{}".format(sqltype, sqltype_list)
        try:
            def creat_conn_id():
                # 创建一个conn_id 链接
                conn_id = dw_basic.dwrun_sqlParse_v1_conn(db_name)
                self.conn_id_dict[db_name].append(conn_id)
                self.conn_id_sqltype_dict[conn_id] = self.default_sqltype
                print(f"新生成sqltype = {self.default_sqltype} 的 一个 conn_id：{conn_id}")
                return conn_id

            # 1、判断当前数据库是否已存在 connId
            if db_name in self.conn_id_dict.keys() and is_new == 0:

                while len(self.conn_id_dict[db_name]) > 0:
                    check_conn_id = self.conn_id_dict[db_name][-1]
                    # 从最新的一个connectID 检查是否可用，不可用就自动移除
                    is_connect = dw_basic.dwrun_sqlParse_v1_conn_heart(check_conn_id)
                    if is_connect is True:
                        conn_id = check_conn_id
                        break
                    else:
                        self.conn_id_dict[db_name].pop()
                        self.conn_id_sqltype_dict.pop(check_conn_id)
                # 处理为空的情况
                if len(self.conn_id_dict[db_name]) <= 0:
                    conn_id = creat_conn_id()
            else:
                conn_id = creat_conn_id()
            print(f"{db_name} 库拥有的conn_id个数为：{len(self.conn_id_dict[db_name])}")
            # 2.判断当前 conn_id的类型为 plsql  或者sqlserver
            if self.conn_id_sqltype_dict[conn_id] != sqltype.lower():
                self.set_connid_session_sqltype(db_name, conn_id, sqltype)
            elif self.test_onOff == "true":  # 此为true时，需每次都要设置一下 set session
                self.set_connid_session_sqltype(db_name, conn_id, sqltype)
            return conn_id
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 初始化创建某个表(从配置文件中dwrun_plsql.ini 文件中获取)
    def initialize_table(self, db_name, tb_name, conn_id):
        """
        str db_name:  数据库名字
        str tb_name:  表名字
        str conn_id: 数据库连接的关键字
        int is_save: 0为不保存，1为保存   （保存到当前类）
        :return: None
        """
        try:
            # 1、根据表名，从配置文件获取sql语句
            sqltyp = self.conn_id_sqltype_dict[conn_id]
            table_dict = self.get_sql_path_info(tb_name, sqltype=sqltyp)
            sql_list = list(table_dict.values())
            # 根据顺序
            start_time = time.time()
            for sql in sql_list:
                data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql, conn_id)
                assert data_dict['result'] == 0, f"执行sql（{sql}）语句失败：\n{data_dict}"
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 初始化创建某个表(并对表名重命名)(从配置文件中dwrun_plsql.ini 文件中获取)
    def initialize_table_rename(self, db_name, conn_id, tb_name_old, tb_name_new):
        """
        str db_name:  数据库名字
        str tb_name_old:  原表名字（dwrun_plsql.ini  中配置的 section）
        str tb_name_new: 要把表改成的新名字
        str conn_id: 数据库连接的关键字
        int is_save: 0为不保存，1为保存   （保存到当前类）
        :return: None
        """
        try:
            # 1、根据表名，从配置文件获取sql语句
            sqltyp = self.conn_id_sqltype_dict[conn_id]
            table_dict = self.get_sql_path_info(tb_name_old, sqltype=sqltyp)
            sql_list = list(table_dict.values())
            partn = re.compile(fr"\s+{tb_name_old}")
            # 根据顺序
            tb_name_new += " "  # 因sql语句表名前一般都有空格，所以加一个
            for sql in sql_list:
                sql1 = re.sub(partn, tb_name_new, sql)  # 替换字符串
                data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql1, conn_id)
                assert data_dict['result'] == 0, f"执行sql（{sql}）语句失败：\n{data_dict}"
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 检查多个表是否在库中，若不在库中,就初始化这些表(从配置文件中dwrun_plsql.ini 文件中获取)
    def check_tables_initialize(self, db_name, tb_name_list, conn_id, tb_rename_list=[], is_force_init=0):
        """
        检查多个表是否在库中，若不在库中,就初始化这些表(tb_rename_list!=[]，就对这些表进行重命名)
        str db_name:  数据库名字
        str/list tb_name_list:  表名字/表名list
        str conn_id: 数据库连接的关键字
        list tb_rename_list:对表名重命名的list，注意顺序需要与tb_name_list对应上 、
        int is_force_init:是否强制初始化，0为不强制，1为强制（tb_rename_list会影响 强制）
        :return: None
        """
        try:
            # 处理参数 tb_name_list
            tb_name_list_type = type(tb_name_list)
            if tb_name_list_type == str:
                tb_name_array = (tb_name_list,)
            elif tb_name_list_type in (list, tuple):
                tb_name_array = tuple(tb_name_list)
            else:
                pass

            if tb_rename_list:  # 需要重名名时，会自动进行强制初始化
                is_force_init = 1

            for index, tb_name in enumerate(tb_name_array):
                # 1、检查表是否在库中
                db_table_list = dw_basic.dwrun_sqlParse_v1_tbls(db_name,
                                                                data={'key': tb_name, 'pageNum': 1, 'pageSize': 100})
                if tb_name not in db_table_list or is_force_init == 1:
                    if tb_rename_list:
                        self.initialize_table_rename(db_name, conn_id, tb_name, tb_rename_list[index])
                    else:
                        self.initialize_table(db_name, tb_name, conn_id)
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # 检查多个表是否在库中，在库中就删除该表；同时返回exist_dict字典，1为存在0为不存在
    def check_tables_drop(self, db_name, tb_name_list, conn_id, is_drop=1):
        """
        检查多个表是否在库中，在库中就删除该表
        str db_name:  数据库名字
        str/list tb_name_list:  表名字/表名list
        str conn_id: 数据库连接的关键字
        int is_drop:是否删除（1为删除，0为不删除）
        :return: exist_dict 返回表存在的字典，1为存在，0为不存在
        """
        try:
            # 处理参数 tb_name_list
            tb_name_list_type = type(tb_name_list)
            if tb_name_list_type == str:
                tb_name_array = (tb_name_list,)
            elif tb_name_list_type in (list, tuple):
                tb_name_array = tuple(tb_name_list)
            else:
                pass
            exist_dict = {}
            for tb_name in tb_name_array:
                print(f"准备检查表：{tb_name}")
                # 1、检查表是否在库中
                tb_name = tb_name.strip()
                db_table_list = dw_basic.dwrun_sqlParse_v1_tbls(db_name,
                                                                data={'key': tb_name, 'pageNum': 1, 'pageSize': 100})
                if tb_name in db_table_list:
                    exist_dict[tb_name] = 1  # 存在为1
                    if is_drop == 1:
                        self.sql_drop_table(db_name, conn_id, tb_name)
                else:
                    exist_dict[tb_name] = 0  # 不存在为0
            print(f"exist_dict:{exist_dict}")
            return exist_dict
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # sql 查询某个库，都有哪些表，返回一个list
    def sql_show_tables(self, db_name, conn_id):
        """
        str db_name:  数据库名字
        str conn_id: 数据库连接的关键字
        :return: list
        """
        try:
            # 查询该库所拥有的表
            data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql='show tables', connId=conn_id)
            data_dict = data_dict['data']
            table_list = []
            if data_dict:
                for t in data_dict:
                    table_list.append(t[0])

            print(f"查询库:{db_name},已经创建的表返回信息为：{table_list}")
            return table_list
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # sql 库不存在表，就建立一个空表(无数据)
    def sql_creat_table_nodata(self, db_name, conn_id, sql=None):
        """
        str db_name:  数据库名字
        str conn_id: 数据库连接的关键字
        :return: str table_name
        """
        try:
            # 默认建表sql
            table_name = "scott01" + get_timestamp()
            creat_table = "create table {table_name}(no number(2) PRIMARY KEY,name varchar2(10),loc varchar2(10));"
            # 有表sql
            if sql is None:
                creat_table = sql
            data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql=creat_table, connId=conn_id)
            assert data_dict['result'] == 0, f'{db_name}库创建表{table_name}失败，其信息为：\n{data_dict}'
            return table_name
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # sql 删除表
    def sql_drop_table(self, db_name, conn_id, table_name):
        """
        str db_name:  数据库名字
        str conn_id: 数据库连接的关键字
        str table_name:表名
        :return: str table_name
        """
        try:
            sql = 'drop table if exists {}'.format(table_name)
            data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql=sql, connId=conn_id)
            assert data_dict['result'] == 0, f'{db_name}库删除表{table_name}失败，其信息为：\n{data_dict}'
            return table_name
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    # sql 删除储存过程
    def sql_drop_procedure(self, db_name, conn_id, procedure_name):
        """
        str db_name:  数据库名字
        str conn_id: 数据库连接的关键字
        str procedure_name: 储存过程名字
        :return: str table_name
        """
        try:
            sql = f"drop Procedure {procedure_name}"
            data_dict = dw_basic.dwrun_sqlParse_v1(db_name, sql=sql, connId=conn_id)
            assert data_dict['result'] == 0, f'{db_name}库删除存储过程：{procedure_name}失败，其信息为：\n{data_dict}'
            return procedure_name
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e

    def drop_database(self, db_name: str, connid):
        """
        测试用例执行完成后，删除此次测试所建的数据库
        """
        def get_db_id(db_name):
            """
            根据db_name获取对应的db_id信息
            """
            db_list: List = dw_basic.dw_monitor_dbstat()["dwMonitorDbStatInfo"]["list"]
            for db in db_list:
                if db["dbName"] == db_name:
                    return db["id"]

        try:
            # 查找该库中有哪些表【需要先将表删除完成后，再删除库】
            table_list = dw_basic.dwrun_sqlParse_v1_tbls(dbName=db_name)
            for table in table_list:
                sql = f"drop table if exists {table};"
                dw_basic.dwrun_sqlParse_v1(dbName=db_name, sql=sql, connId=connid)
            # 删除完成后再删除库
            # 将db_name转换成全部大写，请求中db_name全部是大写字母
            upper_dbName = db_name.upper()
            # 获取db_id
            dbID = get_db_id(upper_dbName)
            # 调用删库接口，将id和dbname传进去
            data_dict = dw_basic.delete_dwdesign_dbManager_v1_dbs(dbID=dbID, dbName=upper_dbName)["data"]
            if data_dict == "success":
                return True
            else:
                return False
        except Exception as e:
            dw_basic.hdba.except_deal(e, traceback.format_exc())
            raise e
        pass


sdc_dw = SdcDw()

if __name__ == "__main__":
    from api.http.sdp_manage_base import manage_basic

    manage_basic.get_api_auth_checkLogin()
    db_name = sdc_dw.get_dbName_new()
    print(db_name)
