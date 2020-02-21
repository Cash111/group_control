#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/7 10:43 上午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : base_script.py
# @Project : Socialpeta2.0
import time
import asyncio

from uiautomator2 import connect

from group_control.atx_agent.async_api import Device


class BaseScript:
    def __init__(self, *args, **kwargs):
        self.duration = kwargs.get('duration', 0)
        self.timer = dict()
        self.package_name = None
        self.window_size = None
        self._scale = None

    async def start_app(self, d):
        current_app = await d.app_current()
        if self.package_name == current_app['package']:
            await d.app_stop(self.package_name)
        await d.app_start(self.package_name, use_monkey=True)

    def _now(self):
        now = time.time()
        return now

    def current_window_size(self, x, y):
        pass

    def run(self, devices):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.set_task(devices))

    async def set_task(self, devices):
        tasks = list()
        for d in devices:
            connect(d)
            host = devices[d]
            _d = Device(host)
            task = asyncio.ensure_future(self._run(_d))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=False)

    async def _run(self, d):
        self.window_size = await d.window_size
        now = self._now()
        self.timer['start'] = now
        self.timer['end'] = now + self.duration
        while self._now() < self.timer['end']:
            await self.main(d)
        await self.close(d)

    async def close(self, d):
        await d.app_stop(self.package_name)
        await d.sleep(1)
        await d.app_clear(self.package_name)

    async def main(self, d):
        raise NotImplementedError
