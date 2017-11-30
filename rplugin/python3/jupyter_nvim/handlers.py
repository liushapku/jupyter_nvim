import tempfile
import re

__all__ = (
    'MsgHandler',
    'OutBufMsgHandler'
)

# learn from notebook/services/kernels/handlers.py
# learn from notebook/static/services/kernels/kernel.js

_control_seq = re.compile('\x1b\[[0-9;]+m')
def remove_terminal_control_sequence(string):
    return re.sub(_control_seq, '', string)

def handle(channel, msg_type):
    def wrapper(f):
        def wrapped(self, *args, **kwargs):
            return f(self, *args, **kwargs)
        return wrapped
    return wrapper

class MsgHandler():
    def __init__(self, nvim, log):
        self.nvim = nvim
        self.bufs = []
        self.log = log

    def __bool__(self):
        return bool(self.bufs)

    def __call__(self, channel, msg, **kwargs):
        msg_type = msg['header']['msg_type']
        func_name = channel + '_' + msg_type

        content = msg['content']
        if hasattr(self, func_name):
            getattr(self, func_name)(content, msg=msg, **kwargs)
            return True
        else:
            return False

    def get_data(self, content):
        # TODO: handle different mime types
        data = content['data']
        output = data.get('text/plain')
        if output is not None:
            return output

class OutBufMsgHandler(MsgHandler):
    def append(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        for buf in self.bufs:
            self.nvim.async_call(buf.append, lines)

    def on_finish_kernel_info(self, kernel_info, pending_shell_msgs, pending_iopub_msgs):
        self.append(kernel_info['banner'])
        for msg in pending_shell_msgs:
            self('shell', msg)
        for msg in pending_iopub_msgs:
            # self.log.info(msg)
            self('iopub', msg)

    def format_input(self, execution_count, string):
        lines = string.split('\n')
        header1 = 'In  [{}]: '.format(execution_count)
        headers = ' ' * (len(header1)-5) + '...: '
        rv = []
        rv.append(header1 + lines[0])
        for line in lines[1:]:
            rv.append(headers + line)
        return rv

    def format_output(self, execution_count, string):
        lines = string.split('\n')
        header = 'Out [{}]:'.format(execution_count)
        if len(lines) > 1:
            lines.insert(0, header)
        else:
            lines = [header + ' ' + lines[0]]
        # add a new line after output
        lines.append('')
        return lines

    ### SHELL messages
    def shell_inspect_reply(self, content, **kwargs):
        if content['status'] == 'ok' and content['found']:
            data = self.get_data(content)
            data = remove_terminal_control_sequence(data)
            self.append(data)

    ### IOPUB messages
    def iopub_execute_input(self, content, **kwargs):
        code = self.format_input(content['execution_count'], content['code'])
        self.append(code)

    def iopub_execute_result(self, content, **kwargs):
        output = self.get_data(content)
        if output:
            output = self.format_output(content['execution_count'], output)
            self.append(output)

    def iopub_error(self, content, **kwargs):
        message = '{}: {}'.format(content['ename'], content['evalue'])
        self.append(message.split('\n'))
        traceback = [remove_terminal_control_sequence(line) for line in content['traceback']]
        def set_traceback(nvim, traceback):
            self.log.error('%s %s', type(nvim.api.vars), type(nvim))
            nvim.vars['jupyter_nvim_traceback'] = traceback
            nvim.command('cgetexpr jupyter_nvim_traceback')
        self.nvim.async_call(set_traceback, self.nvim, traceback)

    def iopub_stream(self, content, msg, **kwargs):
        content = msg['content']
        stream = content['text'].split('\n')
        if stream and stream[-1] == '':
            stream.pop(-1)
        self.append(stream)
