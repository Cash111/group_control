#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/20 5:08 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : facebook.py
# @Project : Socialpeta2.0


import time

from group_control.scripts.base_script import BaseScript


class FacebookScript(BaseScript):

    def main(self, d):
        # d = connect_device()
        d.press('home')
        time.sleep(1)
        d.swipe_ext("right")
        print('DouyinScript done')