#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/20 5:41 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : index.py
# @Project : Socialpeta2.0
import aiohttp_jinja2


class IndexHandler:
    def __init__(self, task_handler):
        self.task_handler = task_handler

    async def index(self, request):
        return aiohttp_jinja2.render_template("index.html", request, locals())

    async def schedule_task(self, request):
        scripts, devices = self.task_handler.selected_scripts, self.task_handler.selected_devices
        return aiohttp_jinja2.render_template("schedule_task.html", request, locals())
