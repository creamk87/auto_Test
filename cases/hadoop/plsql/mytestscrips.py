#!/usr/bin/env python
# -*- coding:utf8 -*-
from utils import *

path = get_datas_path() + "\\Hadoop\\01PLSQL_operational_data.yml"
json_data = read_yaml(path=path)
data = parse_yaml(json_data=json_data)
for item in data:
    print(type(item["assert"]))
