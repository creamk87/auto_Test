import allure
import pytest
from utils import *
from pathlib import Path
from util.mysqlcon import *


class TestTSDB:
    dates_path = get_datas_path() + "/TSDB/"
    # print(Path(dates_path))
    create_db_datas = read_yaml(dates_path + str(Path("/01TSDB_create_db.yml")))

    @classmethod
    def setup_class(cls):
        """
        创建mysql数据库连接
        :return: None
        """
        try:
            cls.db_obj = MySql()
            cls.db_obj.create_connect()
            print("数据库连接创建成功")
        except Exception as e:
            raise Exception(f"数据库连接创建失败，错误信息{e}")

    @classmethod
    def teardown_class(cls):
        """
        关闭数据库连接
        :return: None
        """
        cls.db_obj.close_connect

    @pytest.mark.parametrize("case",
                             [item for item in parse_yaml(create_db_datas)],
                             ids=[item["module_case_name"] for item in parse_yaml(create_db_datas)])
    @allure.story("tsdb_ddl_建库")
    def test_create_db(self, case):
        """
        创建数据库测试用例
        :param case: {
                    'module_name': 'tsdb_ddl_建库',
                    'module_case_name': '创建和检查一个新的库',
                    'name_id': 'create_database_01',
                    'isRun': 1,
                    'db_tb_name':
                        {
                        'db_name': 'rocdb',
                        'tb_name': 'roctb'
                        },
                    'exec_order': ['sql', 'check_td', 'sql1', 'check_td'],
                    'exec_sql':
                        {
                            'sql': 'create database {db_name}',
                            'check_td': 'show databases',
                            'sql1': 'drop database if exists {db_name}'
                        }
                    }
        """
        print(case)
        if case["isRun"] == 1:
            with allure.step("获取测试用例中的输入参数"):
                db_name: str = case["db_tb_name"]["db_name"]
                tb_name: str = case["db_tb_name"]["tb_name"]
                exec_order: List = case["exec_order"]
                exec_sql: Dict = case["exec_sql"]
                # expect_result: List = case["expect_result"]
            with allure.step("开始执行测试用例"):
                tag = 0
                for item in exec_order:
                    if item != "check_td":
                        with allure.step("开始执行sql"):
                            exec_sql[item]: str = exec_sql[item].replace("{db_name}", str(db_name))
                            print(exec_sql[item])
                            sql_result = self.db_obj.execute_sql(exec_sql[item])
                            print(list(sql_result))
                            tag += 1
                    else:
                        with allure.step("开始断言sql执行结果"):
                            exec_sql[item]: str = exec_sql[item].replace("{db_name}", str(db_name))
                            print(exec_sql[item])
                            sql_result = self.db_obj.execute_sql(exec_sql[item])
                            print(list(sql_result))
                            if tag == 1:
                                assert db_name in sql_result
                            elif tag == 2:
                                assert db_name not in sql_result

    def test_create_table(self):
        # print("======还没有写东西=======")
        pass
