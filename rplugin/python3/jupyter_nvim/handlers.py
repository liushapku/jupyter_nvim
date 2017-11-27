__all__ = (
    'MsgHandler',
    'OutBufMsgHandler'
)

# learn from notebook/services/kernels/handlers.py
# learn from notebook/static/services/kernels/kernel.js
class MsgHandler():
    pass

class OutBufMsgHandler(MsgHandler):
    def __init__(self, nvim, buf, log):
        self.nvim = nvim
        self.buf = buf
        self.log = log
        super(OutBufMsgHandler, self).__init__()

    def __call__(self, channel, msg, **kwargs):
        handled = not self._dispatch(channel, msg, **kwargs)
        if handled:
            msg['handled'] = True
        return handled

    def on_finish_kernel_info(self, kernel_info, pending_iopub_msgs):
        self.buf.append(kernel_info['banner'].split('\n'))
        for msg in pending_iopub_msgs:
            # self.log.info(msg)
            self('iopub', msg)

    def get_execute_output(self, data):
        # TODO: handle different mime types
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

    def _dispatch(self, channel, msg, **kwargs):
        """
        return: True if the msg is not handled
        """
        content = msg.get('content')
        msg_type = msg.get('msg_type')
        parent_header = msg.get('parent_header')
        # if parent_header:
        if msg_type in ['execute_input', 'execute_result']:
            return self.handle_execute(msg_type, content)
        elif msg_type == 'stream':
            return self.handle_stream(content)
        elif msg_type == 'error':
            return self.handle_error(content)
        return True

    def handle_execute(self, msg_type, content):
        if msg_type == 'execute_input':
            code = self.format_input_output(
                True, content['execution_count'], content['code'])
            self.buf.append(code)
        elif msg_type == 'execute_result':
            output = self.get_execute_output(content['data'])
            if output:
                output = self.format_input_output(
                    False, content['execution_count'], output)
                self.buf.append(output)

    def handle_error(self, content, **kwargs):
        message = content['{}: {}'.format(content['ename'], content['evalue'])]
        self.buf.append(message.split('\n'))
        with tempfile.TemporaryFile(mode='w') as tmp:
            print(content['traceback'], file=tmp)
            self.nvim.command('lgetfile ' + tmp.name)

    def handle_stream(self, content):
        stream = content['text'].split('\n')
        if stream and stream[-1] == '':
            stream.pop(-1)
        self.buf.append(stream)
