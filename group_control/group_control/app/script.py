#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/20 5:33 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : script.py
# @Project : Socialpeta2.0
import multiprocessing
import aiohttp_jinja2
import group_control.scripts as sc

from urllib.parse import unquote

from importlib import reload


class ScriptHandler:
    def __init__(self, task_handler):
        self.task_handler = task_handler

    async def scripts_select(self, request):
        reload(sc)
        scripts = self.task_handler.classes()
        if request.method == 'GET':
            scripts_list = list(scripts)
            return aiohttp_jinja2.render_template("scripts.html", request, locals())
        elif request.method == 'POST':
            _data = await request.read()
            _data = unquote(_data.decode())
            data = dict([i.split('=') for i in _data.split('&')])
            script_list = list(data.keys())
            for script in script_list:
                self.task_handler.selected_scripts[script_list.index(script)] = {'script': script, 'duration': int(data[script])}
            scripts, devices = self.task_handler.selected_scripts, self.task_handler.selected_devices
            return aiohttp_jinja2.render_template("schedule_task.html", request, locals())

    async def start_scripts(self, request):
        assert self.task_handler
        if isinstance(self.task_handler.p, multiprocessing.Process):
            if self.task_handler.p.is_alive():
                self.task_handler.p.kill()
        self.task_handler.run_in_new_process()
        return aiohttp_jinja2.render_template("running_state.html", request, locals())

    async def manage_scripts(self, request):
        scripts = self.task_handler.selected_scripts
        return aiohttp_jinja2.render_template("scripts.html", request, locals())
