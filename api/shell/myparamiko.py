#!/usr/bin/env python
# -*- coding:utf8 -*-
import time
import traceback
import paramiko


class MyParamiko:
    pass

    def __init__(self, host, port, username, password):
        self.chan = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh: paramiko.client = None

    def create_ssh(self, compress=False, timeout=15):
        """
        实例化对象
        :return: ssh连接对象
        """
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.ssh.connect(hostname=self.host, username=self.username, password=self.password, port=self.port,
                         compress=compress, timeout=timeout)

    def get_ssh(self, is_save=0):
        """
        获取类的通用ssh
        :param is_save:
        :return:
        """
        if self.ssh is None:
            self.create_ssh()
        else:
            if is_save == 1:
                self.ssh.close()
                self.create_ssh()

    def run_exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, environment=None):

        if self.ssh is None:
            self.create_ssh()
        stdin, stdout, stderr = self.ssh.exec_command(command, bufsize, timeout, get_pty, environment)
        stdout_list = []
        stderr_list = []
        for line in stdout.readlines():
            stdout_list.append(line.strip())
        for line in stderr.readlines():
            stderr_list.append(line.strip())
        return stdout_list, stderr_list

    def get_invoke_shell_result(self, chan=None, symbol='#', timeout=30, recv_ready=False):
        """
        交互性shell 接收数据，返回结果
        :param chan: 交互式 返回的chan get_invoke_shell
        :param symbol: 结尾标志符号，注意末尾一般都需加上空格
        :param timeout: chan.recv 获取数据超长时间 单位秒
        :param recv_ready: 获取数据，是否已经准备好（若为True ）
        :return:
        """
        symbol = symbol.strip() + " "  # 默认都需要加一个空格
        if chan is None:
            chan = self.chan
        buff = ''
        time_out_default = chan.timeout
        chan.settimeout(timeout)  # 设置接收数据时长
        times = 0
        try:
            recv_ready_new = chan.send_ready()
            while recv_ready_new is True and not buff.endswith(symbol):
                time.sleep(0.1)
                try:
                    resp = chan.recv(1024)
                    if not resp:
                        print('无数据返回')
                        break
                except Exception as e:
                    print("resp:{}".format(resp))
                    print("timeout={}s 超时，获取数据,请检查  分隔符symbol={}".format(chan.timeout, symbol))
                    break
                try:  # 进行异常捕捉，如果解码有问题，则换一种解码方式
                    buff += resp.decode('utf8')
                except Exception as e:
                    buff += resp.decode('gb18030')
                    print("decode 解析异常")
                times += 1
                if recv_ready is True:
                    recv_ready_new = True
                else:
                    recv_ready_new = chan.recv_ready()
        except Exception as e:
            print("未知异常:{}".format(traceback.format_exc()))
        finally:
            pass
            chan.settimeout(time_out_default)
        str_list = buff.split('\r\n')
        if timeout > 30:
            time_sleep = timeout / 10 * 0.1
            time_sleep = 3 if time_sleep > 3 else time_sleep
            time.sleep(time_sleep)
        else:
            time.sleep(0.3)
        print(str_list)
        return str_list


if __name__ == '__main__':
    pk = MyParamiko(host="10.0.8.213", port=22, username="admin", password="Cdsf@119")
    ssh = pk.create_ssh(compress=True)
    print(ssh.get_host_keys().keys())
