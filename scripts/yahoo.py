# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/11 1:56 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : yahoo.py
# @Project : Socialpeta2.0

import time

from group_control.scripts.base_script import BaseScript


class YahooScript(BaseScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.package_name = "jp.co.yahoo.android.yjtop"

    def find_article_el(self, d):
        els_pattern_1 = d(resourceId='jp.co.yahoo.android.yjtop:id/topics_article_root')
        els_pattern_2 = d(resourceId='jp.co.yahoo.android.yjtop:id/stream_root')

        if els_pattern_1.count > 1:
            _els = els_pattern_1
        else:
            _els = els_pattern_2
        try:
            if _els.count > 1:
                return _els
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def click_article(self, d, els):
        for el in els:
            el.click()
            time.sleep(5)
            self.swipe(d, direction='up', duration=0.05, times=5)
            d.press('back')
            time.sleep(2)
            return True

    def swipe(self, d, direction='up', duration=0.05, times=1, delay=0):
        for i in range(times):
            self._swipe(d, direction, duration)
            time.sleep(delay)

    def _swipe(self, d, direction='up', duration=0.05):
        if direction == 'up':
            d.swipe(540, 1900, 540, 500, duration)
        elif direction == 'down':
            d.swipe(540, 500, 550, 1900, duration)
        elif direction == 'left':
            d.swipe(150, 1900, 550, 1900, duration)
        else:
            d.swipe(550, 1900, 150, 1900, duration)

    def loading_main_page(self, d):
        i = 5
        while i > 0:
            els = d(resourceId="jp.co.yahoo.android.yjtop:id/tabbar_icon_home")
            if els.exists:
                print('已进入首页')
                return True
            else:
                time.sleep(5)
                i -= 1
        return False

    def wait_for_main_page(self, d):
        i = 10
        while i > 0:
            el = d(resourceId="jp.co.yahoo.android.yjtop:id/tabbar_icon_home")
            if el.exists:
                print('已回到首页')
                return
            else:
                d.press('back')
                i -= 1
        self.start_app(d)

    def main(self, d):
        self.start_app(d)
        els = self.loading_main_page(d)
        if not els:
            return None
        i = 0
        while i <= 6:
            self.swipe(d, direction='up', duration=0.5)
            time.sleep(1)
            article_els = self.find_article_el(d)
            if not article_els:
                self.swipe(d, direction='right')
                i += 1
                continue
            else:
                self.click_article(d, article_els)
            time.sleep(1)
            self.swipe(d, direction='right')
            i += 1
        print("YahooScript done")


if __name__ == '__main__':
    import uiautomator2
    yts = YahooScript()
    _d = uiautomator2.connect('192.168.0.100')
    yts.main(_d)

