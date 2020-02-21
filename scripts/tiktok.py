#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/7 10:43 上午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : tiktok.py
# @Project : Socialpeta2.0
import time

from group_control.scripts.base_script import BaseScript


class TiktokScript(BaseScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.package_name = 'com.ss.android.ugc.trill'

    def main(self, d):
        # d = connect_device()
        d.press('home')
        time.sleep(1)
        d.swipe_ext("left")
        time.sleep(1)
        d.swipe_ext("left")
        print('TiktokScript done')

