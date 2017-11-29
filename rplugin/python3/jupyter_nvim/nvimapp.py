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
    REQUEST = 0

    def format_msg(self, handled, channel, msg):
        buf = io.StringIO()
        if handled:
            start, end = '=' * 4, '=' * 50
        else:
            start, end = '*' * 4, '*' * 50
        print(start, channel, self.msg_count[channel], '-', self.msg_count['all'], end, file=buf)
        msg_time = msg['header']['date']
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
        self.msg_count = {
            'shell': 0,
            'iopub': 0,
            'stdio': 0,
            'hb': 0,
            'all': 0,
        }

        self.execution_list = {}
        self.waiting_list = {}
        self.obuf = set()
        self.ibuf = set()
        self.iobuf = set()
        self.obuf_handler = OutBufMsgHandler(self.nvim, self.log)
        self.iobuf_handler = OutBufMsgHandler(self.nvim, self.log)

    def on_finish_kernel_info(self):
        if self.obuf_handler:
            self.obuf_handler.on_finish_kernel_info(self.kernel_info, self.pending_shell_msg, self.pending_iopub_msg)
        self.pending_shell_msg.clear()
        self.pending_iopub_msg.clear()

    def _get_valid_bufs(self, bufnos):
        buffers = {buf.number : buf for buf in self.buffers if buf.number in bufnos}
        return buffers

    def register_out_buffer(self, *bufnos):
        valid_bufs = self._get_valid_bufs(bufnos)
        added = False
        for bufno, buf in valid_bufs.items():
            if bufno not in self.obuf:
                self.obuf.add(bufno)
                self.obuf_handler.bufs.append(buf)
                added = True
        return added

    def register_in_buffer(self, bufno):
        self.ibuf.add(bufno)

    def register_io_buffer(self, bufno):
        valid_bufs = self._get_valid_bufs(bufnos)
        added = False
        for bufno, buf in valid_bufs:
            if bufno not in self.iobuf:
                self.iobuf.add(bufno)
                self.iobuf_handler.bufs.append(buf)
                added = True
        return added

    def output(self, msg):
        self.log.info(msg)

    def finish_message(self, pid):
        del self.waiting_list[pid]
        self.log.info('message %s finished', pid)

    def handle_msg(self, channel, msg, **kwargs):
        if isinstance(msg, float):
            print(channel, msg)
        self.msg_count[channel] += 1
        self.msg_count['all'] += 1
        if self._inspect_msg:
            self._inspect_msg(msg)

        handled = False
        if self.obuf_handler:
            handled = self.obuf_handler(channel, msg, **kwargs)
        self.log.info(self.format_msg(handled, channel, msg))

    @catch_exception
    def on_shell_msg(self, msg):
        pid = self.get_parent_id(msg)
        own = self.is_waiting_for(pid)
        self.handle_msg('shell', msg, own=own)
        if own:
            assert msg['header']['msg_type'].endswith('_reply')
            self.waiting_list[pid] += 1
            if self.waiting_list[pid] >= 2:
                self.finish_message(pid)

    @catch_exception
    def on_iopub_msg(self, msg):
        pid = self.get_parent_id(msg)
        own = self.is_waiting_for(pid)
        self.handle_msg('iopub', msg, own=own)
        if own:
            # finished
            if msg['header']['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                self.waiting_list[pid] += 1
            if self.waiting_list[pid] >= 2:
                self.finish_message(pid)
        if msg['header']['msg_type'] == 'execute_input':
            self.execution_list[pid] = msg['content']['execution_count']

    @catch_exception
    def on_stdin_msg(self, msg):
        self.handle_msg('stdin', msg)

    @catch_exception
    def on_hb_msg(self, msg):
        self.set_state('dead')
        self.log.warning('heart beat: %f', msg)

    def shell_send_callback(self, method, msgid):
        assert msgid not in self.waiting_list
        self.log.info('waiting for %s', msgid)
        self.waiting_list[msgid] = self.REQUEST

    def get_parent_id(self, msg):
        parent_header = msg.get('parent_header')
        if parent_header:
            return parent_header['msg_id']

    def is_waiting_for(self, parent_id):
        return parent_id in self.waiting_list

    @property
    def buffers(self):
        return self.nvim.buffers


class JupyterNvimApp(JupyterContainerApp):

    child_app_factory = JupyterNvimBufferApp
    classes = JupyterContainerApp.classes + [JupyterNvimBufferApp]

    def _log_default(self):
        from traitlets import log
        logger = log.get_logger()
        logfile = os.environ.get('JUPYTER_NVIM_LOG_FILE').strip()
        if logfile:
            print('logging to', logfile)
            logger.handlers = []
            logger.addHandler(logging.FileHandler(logfile, 'w'))
            logger.level = logging.INFO
        return logger

    def initialize(self, nvim, argv=None):
        assert isinstance(nvim, neovim.api.nvim.Nvim), 'nvim should be an Nvim instance'
        self.nvim = nvim
        super(JupyterNvimApp, self).initialize(argv=argv)
        self.log.info('JupyterNvimApp Initialized')
        self._current = None

    @property
    def buffers(self):
        return self.nvim.buffers

    def start_child_app(self, childid, argv=None, **kwargs):
        # if not any(buf.number == childid for buf in self.buffers):
        #     self.log.error('chilid should be a buf number')
        #     return
        bufapp = super(JupyterNvimApp, self).start_child_app(childid, argv, **kwargs)
        self.log.info('Started child app %d, connection file %s', childid, bufapp.connection_file)
        self.set_current(childid)
        return bufapp

    def set_current(self, childid):
        if childid in self._child_apps:
            self._current = childid
        else:
            self.log.error('child app with id %s does not exist', childid)

    def current_child(self):
        return self._current

