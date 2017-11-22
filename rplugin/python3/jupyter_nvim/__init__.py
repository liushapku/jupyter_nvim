
version_info = (0, 1, 0)
__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])


import neovim
import zerorpc
from jupyter_nvim.nvimapp import (
    JupyterIOPubMessageHandler,
    JupyterNvimBufferApp,
    JupyterNvimApp,
)

@neovim.plugin
@neovim.encoding(True)
class IPythonPlugin(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.zerorpc = zerorpc.Client()
        self.zerorpc.connect("ipc://jupyter-nvim")
        self.zerorpc.print("Initialized")
        # self.app = JupyterNvimApp()
        # self.app.initialize([])

    @neovim.command('JupyterTestCommand')
    def testcommand(self, args, range):
        message = 'Command with args: {}, range: {}'.format(args, range)
        self.nvim.current.line = message
        self.zerorpc.print(message)

    @neovim.function('JupyterTestFunction', sync=True)
    def testfunction(self, args):
        return args

    # allow_nested allows async functions to run when another sync function is being called
    # async function cannot return value
    @neovim.function('JupyterTestAsyncNestedFunction', sync=False, allow_nested=True)
    def testfunction(self, args):
        zerorpc.print('test async nested function')

    @shutdown_hook(f)
    def shutdown_hook(f):
        zerorpc.print('shuting down...')
