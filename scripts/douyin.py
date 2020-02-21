#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/7 10:43 上午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : douyin.py
# @Project : Socialpeta2.0
import time

from group_control.scripts.base_script import BaseScript


class DouyinScript(BaseScript):

    def main(self, d):
        # d = connect_device()
        d.press('home')
        time.sleep(1)
        d.swipe_ext("right")
        print('DouyinScript done')

