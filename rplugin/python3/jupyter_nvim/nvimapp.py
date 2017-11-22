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

import logging
import datetime
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
        self.msg_last = datetime.datetime.now(tz=tzutc())

    def print_msg(self, channel_name, msg, ident=0):
        if ident == 0:
            self.msg_count[channel_name] += 1
            self.msg_count['all'] += 1
            print('====', channel_name,
                  self.msg_count[channel_name], '-', self.msg_count['all'], '=' * 50)
            msg_time = msg['header']['date']
            if msg_time <= self.msg_last:
                print('----', self.msg_last, msg_time)
                pass
            else:
                self.msg_last = msg_time
        for key, val in sorted(msg.items()):
            print(' ' * ident, key, ':', end=' ', sep='')
            if isinstance(val, dict):
                print()
                self.print_msg(channel_name, val, ident=ident+4)
            elif isinstance(val, list):
                if val:
                    print()
                    for ii, item in enumerate(val):
                        print(' '* (ident + 4), item)
                else:
                    print(val)
            else:
                print(val)


    def on_shell_msg(self, msg):
        self.print_msg('shell', msg)

    def on_iopub_msg(self, msg):
        self.print_msg('iopub', msg)

    def on_stdin_msg(self, msg):
        self.print_msg('stdin', msg)

    def on_hb_msg(self, msg):
        self.print_msg('heart', msg)

class JupyterNvimApp(JupyterContainerApp):
    child_app_factory = JupyterNvimBufferApp
    classes = JupyterContainerApp.classes + [JupyterNvimBufferApp]
