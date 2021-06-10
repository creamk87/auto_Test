import sys
import time
import traceback
from collections import namedtuple
import requests


class BaseApi(object):

    def __init__(self, http_client_session=None):
        self.http_client_session = http_client_session or requests.Session()
        self.verify = False  # https证书校验
        self.requests = requests
        self.headers = self.get_default_headers()

    def get_default_headers(self, content_type=1):
        if content_type == 0:
            content_type_format = "json"
        else:
            content_type_format = "x-www-form-urlencoded"
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/{}; charset=UTF-8".format(content_type_format),
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"}
        return headers

    def request(self, method, url, **kwargs):
        if "proxies" in kwargs.keys():
            print("此处使用了代理协议请检查(若未开代理可能会失败！)proxies：{}".format(kwargs['proxies']))
        # DELETE
        methods = ('post', 'put', 'get', 'delete')
        assert method in methods, "输入参数（method）类型错误，其范围在{}".format(methods)
        # 申请一个 nametupe对象                       方法：    开始时间   ，  运行耗时，      响应     #数据大小
        request_meta = namedtuple('RequestsMeta',
                                  ['start_time', 'elapsed_time', 'response', 'content_size', 'status_code'])
        # request_meta = RequestsMeta

        request_meta.start_time = time.time()

        # 开始发起http/https请求
        try:
            if 'verify' not in kwargs.keys():
                kwargs['verify'] = self.verify
            if 'headers' not in kwargs.keys():
                kwargs['headers'] = self.headers
            requests.packages.urllib3.disable_warnings()  # 去掉告警错误
            response = self.http_client_session.request(method, url, **kwargs)
            # response.r
            response.encoding = 'utf-8'
            request_meta.elapsed_time = int((time.time() - request_meta.start_time) * 1000)  # 毫秒
            request_meta.status_code = response.status_code
            request_meta.response = response
            request_meta.content_size = int(response.headers.get("content-length") or 0)
            # 异常处理
            param_info = {"method": method, "url": url, "kwargs": kwargs}
            # print("请检查请求数据为：\n{}\n【返回值】:{}".format( param_info, response.text))
            if request_meta.status_code != 200:
                print(
                    "返回状态码:{}(!=200),，请检查请求：\n{}\n【返回值】:{}".format(request_meta.status_code, param_info, response.text))
        except Exception as e:
            my_request.request_except_deal(e, traceback.format_exc())
            raise e
            # log.error("【错误详细信息】：\n" + traceback.format_exc())

        return request_meta

    def request_except_deal(self, e, result=''):
        """
        #处理接口异常信息
        :param e:   捕获到的异常类
        :return: 异常类型
        """

        except_type = type(e)
        if type(result) != str:
            text = result.response.text
        else:
            text = ""
        return except_type


my_request = BaseApi()
if __name__ == '__main__':
    print("测试", my_request.headers)
