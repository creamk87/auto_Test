import os
import time
from typing import List, Dict

import yaml
import configparser
from pathlib import Path


class Conf(configparser.ConfigParser):
    # 处理读取ini配置文件，option 大小写的问题 可以识别大小写的问题
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        return optionstr


"""
路径获取方法，整合
"""


# 如果不存在定义的日志目录就创建一个
def dirmk(file_path):
    if not os.path.isdir(file_path):
        os.makedirs(file_path)  # 创建多个目录


# 获取工程路径
def get_root_path():
    path = os.path.dirname(os.path.abspath(__file__))
    return str(path)


# 获取config 路径
def get_config_path():
    path = get_root_path() + "/config/"
    dirmk(Path(path))
    return str(Path(path))


# 获取cases路径
def get_cases_path():
    path = get_root_path() + "/cases/"
    return str(Path(path))


# 获取dates路径
def get_datas_path():
    path = get_root_path() + "/dates/"
    return str(Path(path))


# 获取系统版本信息
def get_os_platform():
    """
    posix :linux系统，返回“/”
    nt :windows系统，返回“\”
    java :Java虚拟机，“报错异常”
    """
    sys_info = os.name
    if sys_info == "posix":
        return "/"
    elif sys_info == "nt":
        return "\\"
    else:
        raise Exception("当前系统不支持")


# 配置系统环境变量
# print("appRoot 添加系统变量：")
# sys.path.append(os.getcwd())
# sys.path.append(get_root_path())
# sys.path.append(get_cases_path())


# 读取yaml文件，返回json
def read_yaml(path):
    with open(path, "r+", encoding="utf-8") as f:
        contents = yaml.safe_load(f)
        return contents


def parse_yaml(json_data) -> Dict:
    """
    逐条返回json中的数据
    :param json_data: yaml文件中解析出来的json数据
    :return: json中的每个Dict信息
    """
    for item in json_data:
        yield item


# 获取配置文件，返回字符串
def read_config(file_path, section, option):
    """获取指定路径下的，某个section下的指定 option 对应的值.
    Args:
         str file_path : 配置文件（*.ini）的绝对路径
         str section : 配置文件中的 section
         str option ：配置文件中的 option
    Returns:  str value
    example：
        ini_file_path = appRoot.get_autoTestConfig_path()  # autoTestConfig.ini配置文件卢
        times_default = appRoot.read_config(ini_file_path, "driver", "times")  # 设置浏览器查找元素时，默认等待时间
    """
    conf = Conf()
    conf.read(file_path, encoding='utf-8-sig')
    # 获取指定的section， 指定的option的值
    value = conf.get(section, option)
    return value.strip()


def get_timestamp(format=None):
    # 返回当前系统时间戳  "%y%m%d%H%M%S"  "%Y%m%d%H%M%S"
    format = format if format is not None else "%y%m%d%H%M%S"
    timestamp = time.strftime(format, time.localtime(time.time()))  # 时间戳
    return timestamp


if __name__ == '__main__':
    print("============")
    print(get_root_path())
