#!/usr/bin/env python3
# coding=utf-8
import sys
import os		 
import time		   
import tty
from monitor_terminal import monitor_terminal
import re
from queue import Queue
import threading
import subprocess

passwd = "cvte"
back_que = Queue(maxsize=10)


# ==============================
class user_monitor_adb(monitor_terminal):
    def __init__(self):
        command = ['adb', 'shell']
        monitor_terminal.__init__(self, command)

    def monitor(self, line_stream):
        while True:
            while  back_que.empty() != True:
                back_que.get_nowait()
                self.writen("input keyevent KEYCODE_BACK \n")

    def final(self):
        print("adb at the end")


class UserMonitorCts(monitor_terminal):
    def __init__(self, run_type, test_module, test_range, test_num):
        self.run_type = run_type
        self.test_module = test_module
        self.test_range = test_range
        self.test_num = test_num        
        if run_type == 'cts':
            command = ['sudo', '../android-cts/tools/cts-tradefed'] 
            self.run_type_dir = 'android-cts'
        elif run_type == 'vts' or run_type == "cts-on-gsi":
            command = ['sudo', '../android-vts/tools/vts-tradefed']
            self.run_type_dir = 'android-vts'
        else:
            command = ['../android-gts/tools/gts-tradefed']
            self.run_type_dir = 'android-gts'
        
        
        monitor_terminal.__init__(self, command)
        self.ENTER = True
        self.count = 0


    def create_run_command(self):
        # 当test range 没有选择时，运行全部 test case
        if self.test_range == 1 or self.test_range == 0:
            run_command = "run " + self.run_type + ' --plan ' + self.run_type.upper() + " --skip-preconditions  --disable-reboot \n"
            return run_command
        # 此处为运行单一testcase
        elif self.test_range == 2:
            test_module_list = re.split(',', self.test_module)
            run_command = "run " + self.run_type + " -m " + test_module_list[0] + " -c " + test_module_list[1]
            return run_command
        # 此处为运行特定的模块
        elif self.test_range == 3:
            test_module_list = re.split(",", self.test_module)
            num = len(test_module_list)
            run_command = "run " + self.run_type
            for i in range(num):
                command = " --include-filter " + test_module_list[i]
                run_command = run_command + command
            return run_command

        # 此处为运行排除特定模块的其他模块
        else:
            test_module_list = re.split(",", self.test_module)
            num = len(test_module_list)
            run_command = "run " + self.run_type
            for i in range(num):
                command = " --exclude-filter " + test_module_list[i]
                run_command = run_command + command
            return run_command

    def retry_command(self):

        if self.run_type == "cts" or self.run_type == "gts":
            command = "run retry -r " + str(self.count) + " --disable-reboot \n"
        elif self.run_type == "vts":
            command = "run vts -r " + str(self.count) + " --disable-reboot \n"
        else:
            command = "run cts-on-gsi-retry -r" + str(self.count)+ " --disable-reboot \n"    
        return command

    def monitor_exception(self, line_stream):
        if 'timeout:' in line_stream:
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            return
        if 'TimeoutException' in line_stream:
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            if not back_que.full():
                back_que.put_nowait(1)
            return    
           
        if 'D/ResultReporter: Full Result' in line_stream:
            # 重跑次数
            if self.count >= self.test_num:
                self.set_exit()
            else:
                if "Invocation finished in" in line_stream:
                    if "FAILED: 0" in line_stream:
                        self.set_exit()
                
                # 重跑
                print("re run")
                re_command = self.retry_command()
                print(re_command)
                self.count = self.count + 1


    # 重写的monitor方法，line_stream为终端输出的一行
    def monitor(self, line_stream):
        run_command = self.create_run_command()
        # 环境准备，run_type = 1 为cts
        if self.run_type in ['cts', 'vts', 'cts-on-gsi']:
            if self.ENTER:
                # 自动输入密码进入
                if '[sudo] password for' in line_stream:
                    self.writen(passwd + '\n')
                    return
                # 输入命令开始测试
                if 'Detected new device' in line_stream:
                    self.writen(run_command + '\n')
                    self.ENTER = False
                    return
                    # 测试过程中，判断和相应处理
            else:
                self.monitor_exception(line_stream)
            return

        # gts 测试不用输入sudo，特殊处理
        else:
            if self.ENTER:
                if 'Detected new device' in line_stream:
                    self.writen(run_command + '\n')
                    self.ENTER = False
                    return
                    # 测试过程中，判断和相应处理
            else:
                self.monitor_exception(line_stream)
            return

    def final(self):
        print("xts at the end")


# ==============================
class adb_shell(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.myMonitor = None

    def run(self):
        self.myMonitor = user_monitor_adb()
        self.myMonitor.run()

    def stop(self):
        self.myMonitor.set_exit()


class cts_tf(threading.Thread):
    def __init__(self, run_type, test_module, test_range, test_num):
        threading.Thread.__init__(self)
        self.myMonitor = None
        self.run_type = run_type
        self.test_module = test_module
        self.test_range = test_range
        self.test_num = test_num

    def run(self):
        self.myMonitor = UserMonitorCts(self.run_type,
                                        self.test_module, self.test_range, self.test_num)
        self.myMonitor.run()

    def stop(self):
        self.myMonitor.set_exit()
				   
