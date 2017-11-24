import neovim
from neovim.api.buffer import Buffer, Range
from neovim.api import NvimError
from jupyter_container.application import JupyterChildApp, JupyterContainerApp
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
    "JupyterIOPubMessageHandler",
    "JupyterNvimBufferApp",
    "JupyterNvimApp",
)

def catch_exception(f):
    def wrapper(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except Exception as ex:
            self.log.error('==== EXCEPTION %s', ex)
            buf = io.StringIO()
            traceback.print_tb(sys.exc_info()[2], limit=None, file=buf)
            self.log.error(buf.getvalue())

    return wrapper


class JupyterIOPubMessageHandler():
    def __call__(self, message):
        pass


def client_method(f):
    def wrapped(self, *args, **kwargs):
        assert '_rv' not in kwargs, 'kwargs should not contain _rv'
        client = getattr(self.kernel_client, f.__name__)
        kwargs['_rv'] = client(*args, **kwargs)
        rv = f(self, *args, **kwargs)
        return rv
    return wrapped

class MsgHandler():
    pass

class OutBufMsgHandler(MsgHandler):
    def __init__(self, nvim, buf, log):
        self.nvim = nvim
        self.buf = buf
        self.log = log
        super(OutBufMsgHandler, self).__init__()

    def __call__(self, channel, msg, **kwargs):
        return self.dispatch(channel, msg, **kwargs)

    def get_execute_output(self, data):
        output = data.get('text/plain')
        if output is not None:
            return output

    def format_input_output(self, isinput, execution_count, string):
        lines = string.split('\n')
        header1 = ('In ' if isinput else 'Out') + ' [{}]: '.format(execution_count)
        headers = ' ' * (len(header1)-2) + ': '
        rv = []
        rv.append(header1 + lines[0])
        for line in lines[1:]:
            rv.append(headers + line)

        # add a new line after output
        if not isinput:
            rv.append('')
        return rv

    def dispatch(self, channel, msg, **kwargs):
        content = msg.get('content')
        msg_type = msg.get('msg_type')
        parent_header = msg.get('parent_header')
        if parent_header:
            self.log.warning(msg_type)
            if msg_type == 'execute_input':
                self.buf.append(self.format_input_output(True, content['execution_count'], content['code']))
            elif msg_type == 'execute_result':
                output = self.get_execute_output(content['data'])
                if output:
                    self.buf.append(self.format_input_output(False, content['execution_count'], output))
            elif msg_type == 'stream':
                stream = content['text'].split('\n')
                if stream and stream[-1] == '':
                    stream.pop(-1)
                self.buf.append(stream)
            elif msg_type == 'error':
                self.handle_error(content)

    def handle_error(self, content, **kwargs):
        message = content['{}: {}'.format(content['ename'], content['evalue'])]
        self.buf.append(message.split('\n'))
        with tempfile.TemporaryFile(mode='w') as tmp:
            print(content['traceback'], file=tmp)
            self.nvim.command('lgetfile ' + tmp.name)


class JupyterNvimBufferApp(JupyterChildApp):
    def format_msg(self, channel, msg):
        buf = io.StringIO()
        print('====', channel, self.msg_count[channel], '-', self.msg_count['all'], '=' * 50, file=buf)
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

    # KernelClient.start_channels() fires kernel_info()
    # ThreadedKernelClient adds a _inspect for kernel_info before at the beginning of start_channels
    @catch_exception
    def on_first_shell_msg(self, msg):
        assert msg['msg_type'] == 'kernel_info_reply'
        if self._inspect_msg:
            self._inspect_msg(msg)
        self.log.info(self.format_msg('shell', msg))
        for bufno in self.obuf:
            self.buffers[bufno].append(msg['content']['banner'].split('\n'))
        super(JupyterNvimBufferApp, self).on_first_shell_msg(msg)

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
        self.handle_msg(self, 'shell', msg)

    def on_iopub_msg(self, msg):
        self.handle_msg('iopub', msg)

    def on_stdin_msg(self, msg):
        self.handle_msg('stdin', msg)

    def on_hb_msg(self, msg):
        self.handle_msg('hb', msg)

    @client_method
    def execute(self, *args, **kwargs):
        self.wait_for(kwargs['_rv'])  # _rv is injected by client call
        self.log.info('executing %s', kwargs['_rv'])

    def wait_for(self, msgid):
        assert msgid not in self.waiting_list
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
