#! /usr/bin/env python
# -*- coding: utf-8 -*-
from locust import HttpUser, TaskSet, task
import os


class GetResume(TaskSet):

    @task(1)  # 设置权重值，默认为1，值越大，优先执行
    def get_resume(self):
        # 如果后台需要的是json格式，需要加header，否则报415
        header = {"Content-Type": "application/json"}
        self.client.headers.update(header)
        url1 = "/api/resume/getAllResume"
        json = {'currPage': '1', 'pageSize': '10', 'mark': '0'}
        # 网上是直接把Json的格式填进去，但是在本项目中报400，无法识别数据格式，查看系统报错才明白需要转成json对象
        req = self.client.post(url1, json=json)
        if req.status_code == 200:
            print("success")
        else:
            print("fail")

    @task(1)
    def get_schedule(self):
        header = {"Content-Type": "application/json"}
        url2 = "/api/resume/getAllJobSchedule"
        json = {"currPage": "1", "pageSize": "10"}
        self.client.headers.update(header)
        req = self.client.post(url2, json=json)
        print("Response status code:", req.status_code)
        assert req.status_code == 200


class websitUser(HttpUser):
    tasks = [GetResume]
    min_wait = 3000  # 单位为毫秒
    max_wait = 6000  # 单位为毫秒


if __name__ == "__main__":
    os.system("locust -f locust_test_file.py --host=http://www.baidu.com")
