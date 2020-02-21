#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/7 10:41 上午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : script_system.py
# @Project : Socialpeta2.0

import jinja2
import asyncio
import aiohttp_jinja2
import multiprocessing

from aiohttp import web
import group_control.scripts as sc

from group_control.group_control.app.device import DeviceHandler
from group_control.group_control.app.script import ScriptHandler
from group_control.group_control.app.index import IndexHandler


class TaskHandler:
    def __init__(self):
        self.selected_scripts = dict()
        self.script_classes = self.classes()
        self.timer = dict()
        self.devices = dict()
        self.selected_devices = dict()
        self.p = None

    def classes(self):
        return {c.__name__: c for c in sc.BaseScript.__subclasses__()}

    def switch_script(self, devices):
        sorted(self.selected_scripts)
        while True:
            for script_info in self.selected_scripts.values():
                script, duration = script_info.values()
                try:
                    self.script_classes[script](duration=duration).run(devices)
                except Exception as e:
                    print(e)
                    continue

    def run_in_new_process(self):
        print("启动新进程")
        self.p = multiprocessing.Process(target=self.switch_script, args=(self.selected_devices, ))
        self.p.start()
        print("新进程已启动")


task_handler = TaskHandler()


async def init():
    app = web.Application()
    aiohttp_jinja2.setup(app=app, loader=jinja2.FileSystemLoader(
        '/Users/ql/PythonProjects/Socialpeta2.0/group_control/group_control/templates'))

    index_handler = IndexHandler(task_handler)
    device_handler = DeviceHandler(task_handler)
    script_handler = ScriptHandler(task_handler)

    app.router.add_get('/', index_handler.index)

    app.router.add_get('/schedule', index_handler.schedule_task)

    app.router.add_get('/manage-scripts', script_handler.manage_scripts)
    app.router.add_get('/start-scripts', script_handler.start_scripts)

    app.router.add_get('/scripts-select', script_handler.scripts_select)
    app.router.add_post('/scripts-select', script_handler.scripts_select)

    app.router.add_get('/devices-select', device_handler.devices_select)
    app.router.add_post('/devices-select', device_handler.devices_select)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9099)
    print('\n\tServer started at http://%s:%s...' % ('0.0.0.0', 9099))
    await site.start()

if __name__ == '__main__':
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(init())
    _loop.run_forever()
