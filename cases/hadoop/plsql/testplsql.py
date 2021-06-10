#!/usr/bin/env python
# -*- coding:utf8 -*-
import pytest
from api.http.homePage import hp
from utils import *
import allure


class TestPLSqlManipulateData:
    """
    PLSQL SQL 操纵数据语言查询测试类
    """
    # 获取测试数据路径
    dates_path = get_datas_path() + "\\Hadoop\\"
    operational_data = read_yaml(dates_path + "01PLSQL_operational_data.yml")
    manage_table_data = read_yaml(dates_path + "02PLSQL_manage_table.yml")
    single_function_data = read_yaml(dates_path + "03PLSQL_single_function.yml")
    complex_function_data = read_yaml(dates_path + "04PLSQL_complex_function.yml")
    basic_query_data = read_yaml(dates_path + "05PLSQL_basic_query.yml")
    join_query_data = read_yaml(dates_path + "06PLSQL_join_query.yml")
    sort_query_data = read_yaml(dates_path + "07PLSQL_sort_query.yml")

    @classmethod
    def setup_class(cls):
        """
        执行一次，检查用户是否登录，并初始化数据库
        """
        # 检查登录
        hp.sdp_manage.check_sdp_manage_login()
        # 创建数据库
        cls.db_name = hp.sdc_dw.get_dbName_save(dbType=1)
        cls.conn_id = hp.sdc_dw.dw_basic.dwrun_sqlParse_v1_conn(dbName=cls.db_name)

    @classmethod
    def teardown_class(cls):
        """
        用例执行完成后，删除本次测试新建的库
        """
        status = hp.sdc_dw.drop_database(cls.db_name, cls.conn_id)
        if status is True:
            print(f"{cls.db_name}删除成功")
        elif status is False:
            print(f"{cls.db_name}删除失败")

    def setup_method(self):
        """
        每条用例执行时，检查用户是否登录
        """
        # 检查登录
        hp.sdp_manage.check_sdp_manage_login()

    def initialize_tables(self, isInitialized=0):
        """
        初始化表,导入测试数据
        """
        if isInitialized == 1:
            # 获取初始化数据库的sql语句
            initialize_file_path: str = get_datas_path() + "\\Hadoop\\00Hadoop_initialize_database.yml"
            initialize_sql: Dict = read_yaml(initialize_file_path)
            # 调用方法，进行数据库初始化
            hp.sdc_dw.initialize_tables_plsql(db_name=self.db_name, initialize_sql=initialize_sql)

    def run_case_steps(self, cases):
        """
        运行前3步：
        1、初始化表及数据
        2、获取数据库连接id
        3、获取对应的表、sql语句、语句执行顺序及预期结果
        cases: Dict,测试用例
        return:
            self.conn_id: 数据库连接id
            sqltype: plsql或sqlserver
            tb_name: 测试用到的表名
            exec_order: sql执行顺序
            exec_sql: 执行的sql语句
            expected_result: 预期结果
        """
        with allure.step("初始化表及数据"):
            # 获取用例是否初始化表配置
            isInitialized = cases["isInitialized"]
            # 调用初始化表方法
            self.initialize_tables(isInitialized=isInitialized)
        with allure.step("获取数据库连接id"):
            self.conn_id = hp.sdc_dw.get_dbName_connId(db_name=self.db_name)
            print(f"数据库{self.db_name}连接id为:{self.conn_id}")
        with allure.step("获取对应的表、sql语句、语句执行顺序及预期结果"):
            sqltype = cases["sqltype"]
            tb_name1 = cases["tb_name"]["tb_name1"]  # emp表
            tb_name2 = cases["tb_name"]["tb_name2"]  # dept表
            exec_order = cases["exec_order"]
            exec_sql = cases["exec_sql"]
            expected_result = cases["expected_result"]["data"]
            isCheckHeader = cases["isCheckHeader"]
            expected_header = cases["expected_result"]["header"]
            return self.conn_id, sqltype, tb_name1, tb_name2, exec_order, exec_sql, expected_result, isCheckHeader, expected_header

    def run_case_all_steps(self, cases):
        """
        运行所有步骤：
        1、初始化表及数据
        2、获取数据库连接id
        3、获取对应的表、sql语句、语句执行顺序及预期结果
        4、按顺序执行sql语句，将返回结果与预期结果做对比
        cases: Dict,测试用例
        """
        self.conn_id, sqltype, tb_name1, tb_name2, exec_order, exec_sql, expected_result, isCheckHeader, expected_header = self.run_case_steps(
            cases=cases)
        with allure.step("按顺序执行sql语句，将返回结果与预期结果做对比"):
            for sql in exec_order:
                # tb_name在eval语句中代入使用
                print(f"sql语句:{eval(exec_sql[sql])}")
                hp.sdc_dw.set_session_sqltype(dbName=self.db_name, connId=self.conn_id, sqltype=sqltype)
                data_dict = hp.sdc_dw.dw_basic.dwrun_sqlParse_v1(dbName=self.db_name, sql=eval(exec_sql[sql]),
                                                         connId=self.conn_id)["data"]
                print(f"sql语句执行结果为:\n{data_dict}")
                data_header = hp.sdc_dw.dw_basic.dwrun_sqlParse_v1(dbName=self.db_name, sql=eval(exec_sql[sql]),
                                                                   connId=self.conn_id)["head"]
            assert expected_result == data_dict, f"查询数据与默认查询数据不一致，请检查\nexpected_result: \n{expected_result}\ndata_dict: \n{data_dict}\n"
            if isCheckHeader == 1:
                assert expected_header == data_header, f"查询数据与默认查询数据不一致，请检查\nexpected_header: \n{expected_header}\ndata_dict: \n{data_header}\n"

    @pytest.mark.operationaldata
    @allure.story("SQL 操纵数据语言查询")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(operational_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(operational_data)])
    def test_plsql_update_insert_delete(self, cases):
        """
        执行 SQL 操纵数据语言查询 的测试用例，测试用例从update_insert_delete_data读取
        """
        self.run_case_all_steps(cases=cases)

    @pytest.mark.managetable
    @allure.story("SQL 创建和管理表")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(manage_table_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(manage_table_data)])
    def test_plsql_create_drop_table(self, cases):
        """
        执行 SQL 创建和管理表 的测试用例，测试用例从create_drop_table_data读取
        """
        self.conn_id, sqltype, tb_name1, table2, exec_order, exec_sql, expected_result, isCheckHeader, expected_header = self.run_case_steps(
            cases=cases)
        with allure.step("按顺序执行sql语句，将返回结果与预期结果做对比"):
            for sql in exec_order:
                # tb_name在eval语句中代入使用
                print(f"sql语句:{eval(exec_sql[sql])}")
                hp.sdc_dw.set_session_sqltype(dbName=self.db_name, connId=self.conn_id, sqltype=sqltype)
                data_dict = \
                    hp.sdc_dw.dw_basic.dwrun_sqlParse_v1(dbName=self.db_name, sql=eval(exec_sql[sql]),
                                                         connId=self.conn_id)["data"]
                print(f"sql语句执行结果为:\n{data_dict}")
                if exec_order == "check_td":
                    assert tb_name1 in data_dict, f"查询数据与默认查询数据不一致，请检查\nexpected_result: \n{expected_result}\ndata_dict: \n{data_dict}\n"
                elif exec_order == "check_td1":
                    assert tb_name1 not in data_dict, f"查询数据与默认查询数据不一致，请检查\nexpected_result: \n{expected_result}\ndata_dict: \n{data_dict}\n"

    @pytest.mark.singlefunction
    @allure.story("SQL 单行函数使用")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(single_function_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(single_function_data)])
    def test_plsql_single_function(self, cases):
        """
        执行 SQL 单行函数使用 的测试用例，测试用例从single_function_data读取
        """
        self.run_case_all_steps(cases=cases)

    @pytest.mark.complexquery
    @allure.story("SQL 复杂查询使用")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(complex_function_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(complex_function_data)])
    def test_plsql_complex_function(self, cases):
        """
        执行 SQL 复杂查询使用 的测试用例，测试用例从complex_function_data读取
        """
        self.run_case_all_steps(cases=cases)

    @pytest.mark.basicquery
    @allure.story("SQL 基本查询语句")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(basic_query_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(basic_query_data)])
    def test_plsql_complex_function(self, cases):
        """
        执行 SQL 基本查询语句 的测试用例，测试用例从basic_query_data读取
        """
        self.run_case_all_steps(cases=cases)

    @pytest.mark.joinquery
    @allure.story("SQL 连接查询使用")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(join_query_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(join_query_data)])
    def test_plsql_complex_function(self, cases):
        """
        执行 SQL 连接查询使用 的测试用例，测试用例从join_query_data读取
        """
        self.run_case_all_steps(cases=cases)

    @pytest.mark.sortquery
    @allure.story("SQL 排序数据查询")
    @pytest.mark.parametrize("cases", [item for item in parse_yaml(sort_query_data)],
                             ids=[item["module_case_name"] for item in parse_yaml(sort_query_data)])
    def test_plsql_complex_function(self, cases):
        """
        执行 SQL 排序数据查询 的测试用例，测试用例从sort_query_data读取
        """
        self.run_case_all_steps(cases=cases)

if __name__ == '__main__':
    mytestobj = TestPLSqlManipulateData()
