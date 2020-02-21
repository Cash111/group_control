#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/19 3:49 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : async_atx_test.py
# @Project : Socialpeta2.0
import asyncio

from uiautomator2 import connect
from group_control.atx_agent.async_api import Device
from group_control.scripts.base_script import BaseScript


class YoutubeScript(BaseScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.package_name = "com.google.android.youtube"

    async def click_video(self, d, els=None):
        async def find_video_el():
            _els_1 = d(resourceId="com.google.android.youtube:id/thumbnail_layout")
            _els_2 = d(resourceId="com.google.android.youtube:id/player_overlays")
            try:
                if await _els_1.exist:
                    return _els_1
                elif await _els_2.exist:
                    return _els_2
                else:
                    return None
            except Exception as e:
                print(e)
                return None
        if not els:
            els = await find_video_el()
            if not els:
                return
        el = els[0]
        if el:
            await el.click()
            await d.sleep(5)
            await d.press_key('back')
            await d.sleep(2)
            await d(resourceId="com.google.android.youtube:id/floaty_close_button").click()

    async def loading_main_page(self, d):
        i = 5
        while i > 0:
            _els_1 = d(resourceId="com.google.android.youtube:id/thumbnail_layout")
            _els_2 = d(resourceId="com.google.android.youtube:id/player_overlays")
            if await _els_1.wait_for_exists():
                print('已回到首页')
                return _els_1
            elif await _els_2.exist:
                print('已回到首页')
                return _els_2
            else:
                await d.sleep(5)
                i -= 1
        return None

    async def wait_for_main_page(self, d):
        i = 3
        while i > 0:
            el = d(resourceId="com.google.android.youtube:id/text", text="首页")
            if await el.exists:
                print('已回到首页')
                return
            else:
                await d.press_key('back')
                i -= 1
        # self.start_app(d)

    async def swipe_action(self, d, times=30):
        for _ in range(times):
            await d.swipe(330, 1600, 330, 200, 0.02)
            await d.sleep(2)

    async def main(self, d):
        await self.start_app(d)
        els = await self.loading_main_page(d)
        if els:
            await self.click_video(d, els)
        # self.wait_for_main_page(d)
        await d.sleep(2)
        await self.swipe_action(d, times=20)
        await d.sleep(2)
        await self.click_video(d)
        print('YoutubeScript done')


async def run():
    yts = YoutubeScript()
    devices = {
        '192.168.56.101:5555': '192.168.56.101',
        '192.168.56.102:5555': '192.168.56.102'
    }
    tasks = list()
    for d in devices:
        connect(d)
        host = devices[d]
        _d = Device(host)
        task = asyncio.ensure_future(yts.main(_d))
        tasks.append(task)
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    while True:
        loop.run_until_complete(run())

