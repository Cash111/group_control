#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/2/14 2:51 下午
# @Author : ql
# @Email : qianlei@zingfront.com
# @File : apis.py
# @Project : Socialpeta2.0
import re
import six
import json
import time
import shlex
import hashlib
import logging
import requests

from collections import namedtuple
from urllib.parse import urljoin
from uiautomator2.exceptions import (BaseError, ConnectError, GatewayError, JsonRpcError,
                         NullObjectExceptionError, NullPointerExceptionError,
                         SessionBrokenError, StaleObjectExceptionError,
                         UiaError, UiAutomationNotConnectedError,
                         UiObjectNotFoundError)
from uiautomator2.session import Selector

HTTP_TIMEOUT = 60
logger = logging.getLogger(__name__)


class AtxAgentApi:
    def __init__(self, device):
        self.device = device

    @property
    def json_rpc(self):
        class JSONRpcWrapper:
            def __init__(self, server):
                self.server = server
                self.method = None

            def __getattr__(self, method):
                self.method = method
                return self

            def __call__(self, *args, **kwargs):
                http_timeout = kwargs.pop('http_timeout', HTTP_TIMEOUT)
                params = args if args else kwargs
                return self.server.retry_atx_agent_call(self.method, params,
                                                        http_timeout)

        return JSONRpcWrapper(self)

    @property
    def _touch(self):
        """
        ACTION_DOWN: 0 ACTION_MOVE: 2
        touch.down(x, y)
        touch.move(x, y)
        touch.up()
        """
        ACTION_DOWN = 0
        ACTION_MOVE = 2
        ACTION_UP = 1

        obj = self

        class _Touch(object):
            def down(self, x, y):
                obj.json_rpc.injectInputEvent(ACTION_DOWN, x, y, 0)
                return self

            def move(self, x, y):
                obj.json_rpc.injectInputEvent(ACTION_MOVE, x, y, 0)
                return self

            def up(self, x, y):
                """ ACTION_UP x, y """
                obj.json_rpc.injectInputEvent(ACTION_UP, x, y, 0)
                return self

            def sleep(self, seconds: float):
                time.sleep(seconds)
                return self

        return _Touch()

    def click(self, x, y, duration=None):
        if not duration:
            self.json_rpc.click(x, y)
        else:
            self._touch.down(x, y)
            time.sleep(duration)
            self._touch.up(x, y)

    def swipe(self, fx, fy, tx, ty, duration=0.1, steps=None):
        """
        :param fx: from
        :param fy:
        :param tx: to
        :param ty:
        :param duration:
        :param steps: 步数
        :return:
        """
        rel2abs = self.pos_rel2abs
        fx, fy = rel2abs(fx, fy)
        tx, ty = rel2abs(tx, ty)
        if not steps:
            steps = int(duration * 200)
        return self.json_rpc.swipe(fx, fy, tx, ty, steps)

    @property
    def pos_rel2abs(self):
        size = []

        def convert(x, y):
            assert x >= 0
            assert y >= 0

            if (x < 1 or y < 1) and not size:
                size.extend(
                    self.device.window_size())

            if x < 1:
                x = int(size[0] * x)
            if y < 1:
                y = int(size[1] * y)
            return x, y
        return convert

    def press_key(self, key):
        if isinstance(key, int):
            res = self.json_rpc.pressKeyCode(key)
        else:
            res = self.json_rpc.pressKey(key)
        return res

    def retry_atx_agent_call(self, *args, **kwargs):
        try:
            return self.atx_agent_call(*args, **kwargs)
        except (GatewayError,):
            logger.warning(
                "uiautomator2 is not reponding, restart uiautomator2 automatically",
                RuntimeWarning,
                stacklevel=1)
            self.device.reset_uiautomator("UiAutomator stopped")
        except requests.ReadTimeout as e:
            self.device.reset_uiautomator("Http read-timeout: " + str(e))
        except UiAutomationNotConnectedError:
            self.device.reset_uiautomator("UiAutomation not connected")
        except (NullObjectExceptionError, NullPointerExceptionError,
                StaleObjectExceptionError) as e:
            if args[1] != 'dumpWindowHierarchy':  # args[1] method
                logger.warning(
                    "uiautomator2 raise exception %s, and run code again" % e,
                    RuntimeWarning,
                    stacklevel=1)
            time.sleep(1)
        except requests.ConnectionError:
            logger.info(
                "Device connection is not stable, rerun init-atx-agent ...")
            # if self._connect_method == "usb":
            #     self._init_atx_agent()
            # else:
            raise
        return self.atx_agent_call(*args, **kwargs)

    def atx_agent_call(self, method, params, timeout=15):
        data = {
            "jsonrpc": "2.0",
            "id": self._jsonrpc_id(method),
            "method": method,
            "params": params,
        }
        data = json.dumps(data)
        res = self.request(
            "post",
            self.device.jsonrpc_url,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
            data=data)
        if res.status_code == 502:
            print(res.text)
            raise GatewayError(res, "gateway error")
        if res.status_code == 410:  # http status gone: session broken
            raise SessionBrokenError("app quit or crash", self.device.jsonrpc_url,
                                     res.text)
        if res.status_code != 200:
            raise BaseError(self.device.jsonrpc_url, data, res.status_code, res.text,
                            "HTTP Return code is not 200", res.text)
        jsondata = res.json()
        error = jsondata.get('error')
        if not error:
            return jsondata.get('result')

        err = JsonRpcError(error, method)

        def is_exception(err, exception_name):
            return err.exception_name == exception_name or exception_name in err.message

        if isinstance(
                err.data,
                six.string_types) and 'UiAutomation not connected' in err.data:
            err.__class__ = UiAutomationNotConnectedError
        elif err.message:
            if is_exception(err, 'uiautomator.UiObjectNotFoundException'):
                err.__class__ = UiObjectNotFoundError
            elif is_exception(
                    err,
                    'android.support.test.uiautomator.StaleObjectException'):
                err.__class__ = StaleObjectExceptionError
            elif is_exception(err, 'java.lang.NullObjectException'):
                err.__class__ = NullObjectExceptionError
            elif is_exception(err, 'java.lang.NullPointerException'):
                err.__class__ = NullPointerExceptionError
        raise err

    def _jsonrpc_id(self, method):
        m = hashlib.md5()
        m.update(("%s at %f" % (method, time.time())).encode("utf-8"))
        return m.hexdigest()

    def request(self, method, url, **kwargs):
        headers = kwargs.get('headers', None)
        data = kwargs.get('data', kwargs.get('params'))
        timeout = kwargs.get('timeout', 15)
        resp = requests.request(method=method, url=url, headers=headers, data=data, timeout=timeout)
        return resp


class Device:
    def __init__(self, host='127.0.0.1', port=7912):
        self._host = host
        self._port = port

    @property
    def server_url(self):
        return f"http://{self._host}:{self._port}"

    @property
    def jsonrpc_url(self):
        return f"{self.server_url}/jsonrpc/0"

    @property
    def atx_api(self):
        return AtxAgentApi(self)

    @property
    def window_size(self):
        window_size = self.device_info.get('display', ())
        if window_size:
            window_size = tuple(window_size.values())
        return window_size

    @property
    def device_info(self):
        res = self.atx_api.request('GET', urljoin(self.server_url, 'info'))
        if res.status_code != 200:
            raise
        else:
            info = res.json()
            return info

    @property
    def uiautomator(self):
        return UiAutomator(self)

    def reset_uiautomator(self, reason=None):
        status = self.uiautomator.status
        if not status:
            deadline = time.time() + 40.0
            while time.time() < deadline:
                self.uiautomator.start()
                logger.debug("uiautomator-v2 is starting ... left: %.1fs",
                             deadline - time.time())
                time.sleep(5.0)
                if self.uiautomator.status:
                    return True
            return False

    def click(self, x, y, duration=None):
        self.atx_api.click(x, y, duration)

    def swipe(self, fx, fy, tx, ty, duration=0.1, steps=None):
        self.atx_api.swipe(fx, fy, tx, ty, duration, steps)

    def press_key(self, key):
        return self.atx_api.press_key(key)

    def shell(self, cmdargs, timeout=60):
        def list2cmdline(args: (list, tuple)):
            return ' '.join(list(map(shlex.quote, args)))

        cmdline = list2cmdline(cmdargs) if isinstance(cmdargs, (list, tuple)) else cmdargs
        ret = self._request("post",
                            '/shell',
                            data={
                                'command': cmdline,
                                'timeout': str(timeout)
                            },
                            timeout=timeout + 10)
        if ret.status_code != 200:
            raise RuntimeError(
                "device agent responds with an error code %d" %
                ret.status_code, ret.text)
        resp = ret.json()
        exit_code = 1 if resp.get('error') else 0
        exit_code = resp.get('exitCode', exit_code)
        shell_response = namedtuple("ShellResponse", ("output", "exit_code"))
        return shell_response(resp.get('output'), exit_code)

    def _request(self, method, url, reconnect=True, **kwargs):
        if not url.startswith('http'):
            url = urljoin(self.server_url, url)
        try:
            return self.atx_api.request(method, url, **kwargs)
        except requests.ConnectionError:
            if not reconnect:
                raise
            # self._init_atx_agent()
            return self.atx_api.request(method, url, **kwargs)

    def app_start(self, package_name, extras={}, activity=None, wait=False, use_monkey=False):
        if use_monkey:
            self.shell([
                'monkey', '-p', package_name, '-c',
                'android.intent.category.LAUNCHER', '1'
            ])
            if wait:
                self.app_wait(package_name)
            return

        if not activity:
            info = self.app_info(package_name)
            activity = info['mainActivity']
            if activity.find(".") == -1:
                activity = "." + activity
        args = [
            'am', 'start', '-a', 'android.intent.action.MAIN', '-c',
            'android.intent.category.LAUNCHER'
        ]
        args += ['-n', '{}/{}'.format(package_name, activity)]
        # -e --ez
        extra_args = []
        for k, v in extras.items():
            if isinstance(v, bool):
                extra_args.extend(['--ez', k, 'true' if v else 'false'])
            elif isinstance(v, int):
                extra_args.extend(['--ei', k, str(v)])
            else:
                extra_args.extend(['-e', k, v])
        args += extra_args
        self.shell(args)

        if wait:
            self.app_wait(package_name)

    def app_current(self):
        _focusedRE = re.compile(
            r'mCurrentFocus=Window{.*\s+(?P<package>[^\s]+)/(?P<activity>[^\s]+)\}'
        )
        m = _focusedRE.search(self.shell(['dumpsys', 'window', 'windows'])[0])
        if m:
            return dict(package=m.group('package'),
                        activity=m.group('activity'))

        _activityRE = re.compile(
            r'ACTIVITY (?P<package>[^\s]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)'
        )
        output, _ = self.shell(['dumpsys', 'activity', 'top'])
        ms = _activityRE.finditer(output)
        ret = None
        for m in ms:
            ret = dict(package=m.group('package'),
                       activity=m.group('activity'),
                       pid=int(m.group('pid')))
        if ret:
            return ret
        raise EnvironmentError("Couldn't get focused app")

    def app_info(self, package_name):
        resp = self._request("GET", f"/packages/{package_name}/info")
        resp.raise_for_status()
        resp = resp.json()
        if not resp.get('success'):
            raise BaseError(resp.get('description', 'unknown'))
        return resp.get('data')

    def app_wait(self, package_name, timeout=15, front=False):
        pid = None
        deadline = time.time() + timeout
        while time.time() < deadline:
            if front:
                if self.app_current()['package'] == package_name:
                    pid = self._pid_of_app(package_name)
                    break
            else:
                if package_name in self.app_list_running():
                    pid = self._pid_of_app(package_name)
                    break
            time.sleep(1)

        return pid or 0

    def app_clear(self, package_name):
        self.shell(['pm', 'clear', package_name])

    def app_list_running(self) -> list:
        """
        Returns:
            list of running apps
        """
        output, _ = self.shell(['pm', 'list', 'packages'])
        packages = re.findall(r'package:([^\s]+)', output)
        process_names = re.findall(r'([^\s]+)$',
                                   self.shell('ps; ps -A').output, re.M)
        return list(set(packages).intersection(process_names))

    def _pid_of_app(self, package_name):
        text = self._request("get", '/pidof/' + package_name).text
        if text.isdigit():
            return int(text)

    def app_stop(self, package_name):
        self.shell(['am', 'force-stop', package_name])

    def __call__(self, **kwargs):
        return UiObj(self, Selector(**kwargs))


class UiAutomator:
    def __init__(self, device):
        self.device = device
        
    @property
    def status(self):
        res = self.device.atx_api.request(method='GET', url=self.server_url)
        if res.status_code != 200:
            raise
        else:
            running = res.json().get('running', False)
            return running

    @property
    def server_url(self):
        return urljoin(self.device.server_url, 'services/uiautomator')

    def start(self):
        res = self.device.atx_api.request(method='POST', url=self.server_url)
        if res.status_code != 200:
            raise
        else:
            res = res.json()
            desc = res.get('description')
            print(desc)
            success = res.get('success', False)
            return success

    def stop(self):
        res = self.device.atx_api.request(method='DELETE', url=self.server_url)
        if res.status_code != 200:
            raise
        else:
            res = res.json()
            desc = res.get('description')
            print(desc)
            success = res.get('success', False)
            return success


class UiObj:
    def __init__(self, device, selector, wait_timeout=15):
        self.device = device
        self.selector = selector
        self.wait_timeout = wait_timeout

    @property
    def exist(self):
        res = self.atx_json_rpc.exist(self.selector)
        return res

    @property
    def atx_api(self):
        return self.device.atx_api

    @property
    def atx_json_rpc(self):
        return self.device.atx_api.json_rpc

    @property
    def info(self):
        res = self.atx_json_rpc.objInfo(self.selector)
        return res

    @property
    def count(self):
        res = self.atx_json_rpc.count(self.selector)
        return res

    def wait_for_exists(self, timeout=15):
        res = self.atx_json_rpc.waitForExists(self.selector, int(timeout*1000))
        return res

    def bounds(self):
        obj_info = self.info
        bounds = obj_info.get('bounds', dict())
        return bounds

    def click(self):
        res = self.atx_json_rpc.click(self.selector)
        return res

    def set_text(self, text=None):
        if text:
            self.atx_json_rpc.setText(self.selector, text)
        else:
            self.atx_json_rpc.clearTextField(self.selector)

    def center(self):
        bounds = self.bounds()
        bottom, left, right, top = bounds['bottom'], bounds['left'], bounds['right'], bounds['top']
        x = (left + right)/2
        y = (bottom + top)/2
        return x, y

    def __bool__(self):
        return self.exist

    def __len__(self):
        return self.count

    def __getitem__(self, index):
        if isinstance(self.selector, six.string_types):
            raise IndexError(
                "Index is not supported when UiObject returned by child_by_xxx"
            )
        selector = self.selector.clone()
        selector.update_instance(index)
        return UiObj(self, selector)

    def __iter__(self):
        obj, length = self, self.count

        class Iter(object):
            def __init__(self):
                self.index = -1

            def next(self):
                self.index += 1
                if self.index < length:
                    return obj[self.index]
                else:
                    raise StopIteration()

            __next__ = next

        return Iter()


if __name__ == '__main__':
    d = Device('192.168.56.101')
    el = d(text='图库').click()
    print(el)
    # print(e)
    # d(resourceId="com.android.quicksearchbox:id/search_src_text").set_text('bba')
    # _status = d.uiautomator.stop()
    # d.click(_x, _y)
    # d.click(332, 1306)
    # d.swipe(967, 1115, 148, 875, duration=0.1)
