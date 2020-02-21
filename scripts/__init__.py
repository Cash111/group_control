#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/7 10:40 上午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : __init__.py.py
# @Project : Socialpeta2.0

from .base_script import BaseScript
from .douyin import DouyinScript
from .tiktok import TiktokScript
from .youtube import YoutubeScript
from .yahoo import YahooScript
from .facebook import FacebookScript

__all__ = ["BaseScript", "DouyinScript", "YoutubeScript", "TiktokScript", "YahooScript", "FacebookScript"]
