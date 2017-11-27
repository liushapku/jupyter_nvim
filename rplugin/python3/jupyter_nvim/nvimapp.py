import neovim
from neovim.api.buffer import Buffer, Range
from neovim.api import NvimError
from jupyter_container.application import (
    JupyterChildApp, JupyterContainerApp, ClientMethodMixin,
    catch_exception
)
from jupyter_nvim.handlers import *
import os
import sys, traceback
import json
import re
from functools import partial, wraps
from collections import deque
import threading
import traitlets

import logging
import datetime
import io
import tempfile
from dateutil.tz import tzutc

__all__ = (
    "JupyterNvimBufferApp",
    "JupyterNvimApp",
)
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




class JupyterNvimBufferApp(JupyterChildApp):
    def format_msg(self, channel, msg):
        buf = io.StringIO()
        if msg.pop('handled', False):
            start, end = '=' * 4, '=' * 50
        else:
            start, end = '*' * 4, '*' * 50
        print(start, channel, self.msg_count[channel], '-', self.msg_count['all'], end, file=buf)
        msg_time = msg['header']['date']
        if msg_time <= self.msg_last:
            print('----', self.msg_last, msg_time, file=buf)
        else:
            self.msg_last = msg_time
        return self._format_msg(buf, channel, msg)

    def _format_msg(self, buf, channel, msg, ident=0):
        for key, val in sorted(msg.items()):
            print(' ' * ident, key, ':', end=' ', sep='', file=buf)
            if isinstance(val, dict):
                print(file=buf)
                self._format_msg(buf, channel, val, ident=ident+4)
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

    def initialize(self, parent, identity, argv=None):
        super(JupyterNvimBufferApp, self).initialize(parent, identity, argv=argv)

        self.nvim = self.parent.nvim
        self._inspect_msg = None
        self.msg_last = datetime.datetime.now(tz=tzutc())
        self.msg_count = {
            'shell': 0,
            'iopub': 0,
            'stdio': 0,
            'hb': 0,
            'all': 0,
        }

        self.waiting_list = set()
        self.buf_handlers = []
        self.obuf = set()
        self.ibuf = set()
        self.iobuf = set()

    def on_finish_kernel_info(self, kernel_info, pending_iopub_msg):
        for handler in self.buf_handlers:
            handler.on_finish_kernel_info(kernel_info, pending_iopub_msg)


    def register_out_vim_buffer(self, bufno):
        if bufno not in self.obuf:
            self.obuf.add(bufno)
            self.buf_handlers.append(OutBufMsgHandler(self.nvim, self.buffers[bufno], self.log))

    def register_in_vim_buffer(self, bufno):
        self.ibuf.add(bufno)

    def register_io_vim_buffer(self, bufno):
        self.iobuf.add(bufno)

    def output(self, msg):
        self.log.info(msg)

    @catch_exception
    def handle_msg(self, channel, msg, **kwargs):
        self.msg_count[channel] += 1
        self.msg_count['all'] += 1
        if self._inspect_msg:
            self._inspect_msg(msg)

        for handler in self.buf_handlers:
            handler(channel, msg, **kwargs)
        self.log.info(self.format_msg(channel, msg))

    def on_shell_msg(self, msg):
        self.handle_msg('shell', msg)

    def on_iopub_msg(self, msg):
        self.handle_msg('iopub', msg)

    def on_stdin_msg(self, msg):
        self.handle_msg('stdin', msg)

    def on_hb_msg(self, msg):
        self.handle_msg('hb', msg)

    def shell_send_callback(self, msgid):
        assert msgid not in self.waiting_list
        self.log.info('waiting for %s', msgid)
        self.waiting_list.add(msgid)

    def is_waiting_for(self, parent_header):
        if parent_header:
            return parent_header.get('msg_id') in self.waiting_list
        return False

    @property
    def buffers(self):
        return self.nvim.buffers


class JupyterNvimApp(JupyterContainerApp):

    child_app_factory = JupyterNvimBufferApp
    classes = JupyterContainerApp.classes + [JupyterNvimBufferApp]

    def _log_default(self):
        from traitlets import log
        logger = log.get_logger()
        if 'JUPYTER_NVIM_LOGFILE' in os.environ:
            print('logging to', os.environ['JUPYTER_NVIM_LOGFILE'])
            logfile = os.environ['JUPYTER_NVIM_LOGFILE'].strip()
            logger.handlers = []
            logger.addHandler(logging.FileHandler(logfile, 'w'))
            logger.level = logging.INFO
        return logger

    def initialize(self, nvim, argv=None):
        assert isinstance(nvim, neovim.api.nvim.Nvim), 'nvim should be an Nvim instance'
        self.nvim = nvim
        super(JupyterNvimApp, self).initialize(argv=argv)
        self.log.info('JupyterNvimApp Initialized')

    @property
    def buffers(self):
        return self.nvim.buffers

    def start_child_app(self, childid, argv=None, **kwargs):
        if not any(buf.number == childid for buf in self.buffers):
            self.log.error('chilid should be a buf number')
            return
        bufapp = super(JupyterNvimApp, self).start_child_app(childid, argv, **kwargs)
        bufapp.register_out_vim_buffer(childid)
        self.log.info('Started child app %d, connection file %s', childid, bufapp.connection_file)
        return bufapp

    def current_child(self):
        current_buf = self.nvim.current.buffer.number
        if current_buf in self._child_apps:
            return current_buf

