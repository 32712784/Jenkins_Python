# coding=utf8
import configparser
import datetime
import logging
import os
import re
import json

import requests
from jenkinsapi.jenkins import Jenkins


def log():
    # 创建logger，如果参数为空则返回root logger
    logger = logging.getLogger("wup")
    logger.setLevel(logging.DEBUG)  # 设置logger日志等级

    # 如果存在logger.handlers列表为0，则创建handler
    if len(logger.handlers) == 0:
        # 创建handler
        fh = logging.FileHandler("log.txt", encoding="utf-8")  # 输出日志保存到文件
        ch = logging.StreamHandler()  # 日志打印到窗口

        # 设置输出日志格式
        formatter = logging.Formatter(
            fmt="%(asctime)s %(name)s %(filename)s %(message)s",
            datefmt="%Y/%m/%d %X")

        # 为handler指定输出格式
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 为logger添加的日志处理器
        logger.addHandler(fh)
        logger.addHandler(ch)

    # 直接返回logger
    return logger


def get_jk_config(chose):
    config = configparser.ConfigParser()
    config.read(os.path.join(os.getcwd(), 'jenkins_server.ini'))
    username = config.get(chose, 'username')
    password = config.get(chose, 'password')
    host = config.get(chose, 'host')
    port = config.get(chose, 'port')
    url = "http://" + host + ":" + port
    return url, username, password

class JenkinsDemo:
    def __init__(self, job_name, chose='jenkins'):
        self.job_name = job_name
        config = get_jk_config(chose)
        self.jk = Jenkins(*config, useCrumb=True)

    def __get_job_from_keys(self):
        choose_list = []
        #得到一个list，任务列表 ['01_持续集成UI自动化', '02_持续集成Appium自动化', '03_持续集成Interface自动化', '04_持续集成performance自动化', '05_AndroidSampleApp', '05_AndroidSampleAppDeploy_BVT']
        print(self.jk.keys())
        for my_job_name in self.jk.keys():
            if self.job_name in my_job_name:
                choose_list.append(my_job_name)
        return choose_list

    def __job_build(self, my_job_name):
        # 判断my_job_name是否存在，会返回True或False
        if self.jk.has_job(my_job_name):
            # 返回job任务对象
            my_job = self.jk.get_job(my_job_name)
            # print(my_job.get_build(5).get_changeset_items())
            # 查询job任务对象是否在运行
            if not my_job.is_queued_or_running():
                try:
                    last_build = my_job.get_last_buildnumber()
                except:
                    last_build = 0
                build_num = last_build + 1
                # 开始打包
                try:
                    self.jk.build_job(my_job_name)
                except Exception as e:
                    log().error(str(e))
                # 循环判断Jenkins是否打包完成
                while True:
                    if not my_job.is_queued_or_running():
                        # 获取最新一次构建信息
                        count_build = my_job.get_build(build_num)
                        # 获取打包开始时间
                        start_time = count_build.get_timestamp() + datetime.timedelta(hours=8)
                        # 获取打包日志
                        console_out = count_build.get_console()
                        # 获取状态
                        status = count_build.get_status()
                        # 获取构建耗时
                        duration = count_build.get_duration()
                        # 获取变更内容
                        change = count_build.get_changeset_items()
                        log().info(f" " + str(start_time) + " 发起的" + my_job_name + "构建已经完成，构建耗时：" + str(duration) + "！")
                        p2 = re.compile(r".*ERROR.*")
                        err_list = p2.findall(console_out)
                        log().info("打包日志为： "+str(console_out))
                        if status == "SUCCESS":
                            if len(change) > 0:
                                for data in change:
                                    for file_list in data["affectedPaths"]:
                                        log().info(" 发起的"+my_job_name+" 变更的类： "+file_list)
                                    log().info(" 发起的"+my_job_name+" 变更的备注： "+data["msg"])
                            else:
                                log().info(" 发起的"+ my_job_name+" 构建没有变更内容！")
                            if len(err_list) > 0:
                                log().warning(" 构建的"+my_job_name+"构建状态为成功，但包含了以下错误: ")
                                for error in err_list:
                                    log().error(error)
                        else:
                            if len(err_list) > 0:
                                log().warning(" 构建的"+my_job_name+"包含了以下错误: ")
                                for error in err_list:
                                    log().error(error)
                        break
            else:
                log().warning(" 发起的"+my_job_name+" Jenkins is running!")
        else:
            log().warning(" 发起的"+my_job_name+"任务不存在！")

    def run(self):
        my_job_name = self.__get_job_from_keys()
        if len(my_job_name) == 1:
            self.__job_build(my_job_name[0])
        elif len(my_job_name) == 0:
            log().error("输入的job名不正确")

    def test(self, my_job_name):
        build_num = 5
        my_job = self.jk.get_job(my_job_name)
        while True:
            if not my_job.is_queued_or_running():
                # 获取最新一次构建信息
                count_build = my_job.get_build(build_num)
                # 获取打包开始时间
                start_time = count_build.get_timestamp() + datetime.timedelta(hours=8)
                # 获取打包日志
                console_out = count_build.get_console()
                # 获取状态
                status = count_build.get_status()
                # 获取构建耗时
                duration = count_build.get_duration()
                # 获取变更内容
                change = count_build.get_changeset_items()
                log().info(f" " + str(start_time) + " 发起的" + my_job_name + "构建已经完成，构建耗时：" + str(duration) + "！")
                p2 = re.compile(r".*ERROR.*")
                err_list = p2.findall(console_out)
                log().info("打包日志为： \n" + str(console_out))
                if status == "SUCCESS":
                    if len(change) > 0:
                        for data in change:
                            for file_list in data["affectedPaths"]:
                                log().info(" 发起的" + my_job_name + " 变更的类： " + file_list)
                            log().info(" 发起的" + my_job_name + " 变更的备注： " + data["msg"])
                    else:
                        log().info(" 发起的" + my_job_name + " 构建没有变更内容！")
                    if len(err_list) > 0:
                        log().warning(" 构建的" + my_job_name + "构建状态为成功，但包含了以下错误: ")
                        for error in err_list:
                            log().error(error)
                else:
                    if len(err_list) > 0:
                        log().warning(" 构建的" + my_job_name + "包含了以下错误: ")
                        for error in err_list:
                            log().error(error)
                break


jenkins = JenkinsDemo('03_持续集成Interface自动化')
# jenkins.run()
jenkins.test('03_持续集成Interface自动化')
