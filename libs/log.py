#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/20 2:46 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : log.py
# @Project : Socialpeta2.0

import logging

logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)

logger = logging.getLogger('group_control')
logger.setLevel('INFO')

