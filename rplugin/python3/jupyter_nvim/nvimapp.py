import neovim
from neovim.api.buffer import Buffer, Range
from neovim.api import NvimError
from jupyter_container.application import JupyterChildApp, JupyterContainerApp
import os
import sys
import json
import re
from functools import partial, wraps
from collections import deque
import threading

import logging
import datetime
import io
from dateutil.tz import tzutc

logger = logging.getLogger(__name__)
error, debug, info, warn = (logger.error, logger.debug, logger.info, logger.warn,)
if 'NVIM_IPY_DEBUG_FILE' in os.environ:
    logfile = os.environ['NVIM_IPY_DEBUG_FILE'].strip()
    logger.addHandler(logging.FileHandler(logfile, 'a'))
    logger.level = logging.DEBUG

__all__ = (
    "JupyterIOPubMessageHandler",
    "JupyterNvimBufferApp",
    "JupyterNvimApp",
)

def catch_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as ex:
            print('==== EXCEPTION', ex)
    return wrapper


class JupyterIOPubMessageHandler():
    def __call__(self, message):

        pass



class JupyterNvimBufferApp(JupyterChildApp):
    # use kernel_client's following method to send message
    # is_alive
    # execute
    # complete
    # inspect
    # history
    # kernel_info
    # comm_info
    # shutdown
    # is_complete
    # input

    def initialize(self, parent, bufno, argv=None):
        super(JupyterNvimBufferApp, self).initialize(parent, bufno, argv=argv)
        print('==== log.level', self.log.level)
        self.msg_count = {
            'shell': 0,
            'iopub': 0,
            'stdio': 0,
            'heart': 0,
            'all': 0,
        }
        self._inspect_msg = None
        self.msg_last = datetime.datetime.now(tz=tzutc())

    def print_msg(self, channel_name, msg, ident=0, buf=None):
        if ident == 0:
            buf = io.StringIO()
            self.msg_count[channel_name] += 1
            self.msg_count['all'] += 1
            print('====', channel_name,
                  self.msg_count[channel_name], '-', self.msg_count['all'], '=' * 50, file=buf)
            msg_time = msg['header']['date']
            if msg_time <= self.msg_last:
                print('----', self.msg_last, msg_time, file=buf)
            else:
                self.msg_last = msg_time
        for key, val in sorted(msg.items()):
            print(' ' * ident, key, ':', end=' ', sep='', file=buf)
            if isinstance(val, dict):
                print(file=buf)
                self.print_msg(channel_name, val, ident=ident+4, buf=buf)
            elif isinstance(val, list):
                if val:
                    print(file=buf)
                    for ii, item in enumerate(val):
                        print(' '* (ident + 4), item, file=buf)
                else:
                    print(val, file=buf)
            else:
                print(val, file=buf)
        return buf.getvalue()

    def output(self, msg):
        print(msg)

    # KernelClient.start_channels() fires kernel_info()
    # ThreadedKernelClient adds a _inspect for kernel_info before at the beginning of start_channels
    @catch_exception
    def on_first_shell_msg(self, msg):
        assert msg['msg_type'] == 'kernel_info_reply'
        if self._inspect_msg:
            self._inspect_msg(msg)
        print(self.print_msg('shell', msg))
        self.output(msg['content']['banner'])
        super(JupyterNvimBufferApp, self).on_first_shell_msg(msg)

    @catch_exception
    def on_shell_msg(self, msg):
        if self._inspect_msg:
            self._inspect_msg(msg)
        print(self.print_msg('shell', msg))

    @catch_exception
    def on_iopub_msg(self, msg):
        if self._inspect_msg:
            self._inspect_msg(msg)
        # string = self.msg_to_buf('iopub', msg) #.getvalue()
        string = self.print_msg('iopub', msg)
        print(string)

    @catch_exception
    def on_stdin_msg(self, msg):
        if self._inspect_msg:
            self._inspect_msg(msg)
        print(self.print_msg('stdin', msg))

    @catch_exception
    def on_hb_msg(self, msg):
        if self._inspect_msg:
            self._inspect_msg(msg)
        print(self.print_msg('heart', msg))


class JupyterNvimApp(JupyterContainerApp):
    child_app_factory = JupyterNvimBufferApp
    classes = JupyterContainerApp.classes + [JupyterNvimBufferApp]
