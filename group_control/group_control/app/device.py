#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/20 3:32 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : device.py
# @Project : Socialpeta2.0
import adbutils
import aiohttp_jinja2

from urllib.parse import unquote


class Devices:
    def __init__(self):
        self.adb_client = adbutils.AdbClient()

    @property
    def devices(self):
        return {_d.serial: _d.wlan_ip() for _d in self.adb_client.device_list()}

    def __getitem__(self, serial):
        # assert serial in self.devices, KeyError("该设备不存在: {}".format(serial))
        return self.devices.get(serial, None)


class DeviceHandler:
    def __init__(self, task_handler):
        self.task_handler = task_handler

    async def devices_select(self, request):
        _devices = Devices().devices
        if request.method == 'GET':
            devices_list = list(_devices)
            return aiohttp_jinja2.render_template("devices.html", request, locals())
        elif request.method == 'POST':
            _data = await request.read()
            _data = unquote(_data.decode())
            device_serials = dict([i.split('=') for i in _data.split('&')])
            self.task_handler.selected_devices = {serial: _devices[serial] for serial in device_serials.values()}
            scripts = self.task_handler.selected_scripts
            devices = self.task_handler.selected_devices
            return aiohttp_jinja2.render_template("schedule_task.html", request, locals())