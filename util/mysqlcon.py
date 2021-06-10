import configparser as cp
import pymysql
from utils import *


class MySql:

    def __init__(self, database=None, initialize=1):
        """
        初始化MySQL对象，从配置文件中读取相关配置
        """
        # 读取配置文件
        self.config_path = get_config_path() + get_os_platform() + "globalconfig.ini"
        self.inifile = cp.ConfigParser()
        self.inifile.read(self.config_path, encoding="utf-8")

        # 读取具体配置项
        # self.host = self.inifile.get("mysql", "host")  # 另外一组读取配置文件的方式
        self.host = self.inifile["mysql"]["host"]
        self.port = int(self.inifile["mysql"]["port"])
        self.username = self.inifile["mysql"]["username"]
        self.password = self.inifile["mysql"]["password"]
        self.database = database
        self.charset = self.inifile["mysql"]["charset"]
        self.db = None
        self.cur = None
        self.initialize = initialize
        if self.initialize == 1:
            self.initialize_database()

    def close_connect(self):
        """
        关闭数据库连接
        :return: None
        """
        if self.db is not None:
            self.db.close()
            self.db = None

    def create_connect(self, isnew=0):
        """
        创建连接对象，连接数据库
        :return: self.db 数据库连接对象
        :return: self.cur 游标对象
        """
        # 判断是否需要新建连接
        if self.db is not None and isnew == 0:
            return self.db

        # 需要新建连接时，新建连接，并返回
        try:
            self.db = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset=self.charset
            )
            self.cur = self.db.cursor()
        except Exception as e:
            raise Exception(f"数据库连接异常：{e}")
        return self.db, self.cur

    def execute_sql(self, sql):
        """
        执行传入的sql语句，返回sql语句的执行结果
        如果sql语句为创建数据库语句，则返回查询所有库的结果
        :param sql:
        :return:
        """
        sql_list = sql.split()
        condition = sql_list[0] + " " + sql_list[1]
        if condition == "show databases":
            self.cur.execute(condition)
            query_result = self.cur.fetchall()
            query_list = []
            for i in query_result:
                query_list.append(i[0])
            return query_list
        else:
            self.db, self.cur = self.create_connect(isnew=1)
            try:
                self.cur.execute(sql)
                return self.cur.fetchall()
            except Exception as e:
                raise Exception(f"{sql} 执行失败，错误信息。 {e}")

    def initialize_database(self):
        pass


if __name__ == '__main__':
    # mysql = MySql(database="Test_JJ")
    # result = mysql.execute_sql("create table 智能运维_带宽1 (id int primary key auto_increment, name varchar(32) not null, age tinyint unsigned not null);")
    mysql = MySql()
    mysql.create_connect()
    result = mysql.execute_sql("show databases")

    # mysql = MySql()
    # result = mysql.execute_sql("create database TTT character set utf8;")
    print(result)
