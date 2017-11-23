
version_info = (0, 1, 0)
__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])

import os
import neovim
import logging
from jupyter_nvim.nvimapp import (
    JupyterIOPubMessageHandler,
    JupyterNvimBufferApp,
    JupyterNvimApp,
)

logger = logging.getLogger(__name__)
if 'NVIM_IPY_DEBUG_FILE' in os.environ:
    logfile = os.environ['NVIM_IPY_DEBUG_FILE'].strip()
    logger.addHandler(logging.FileHandler(logfile, 'w'))
    logger.level = logging.DEBUG


@neovim.plugin
# @neovim.encoding(True)
class TestPlugin(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.app = JupyterNvimApp()
        self.app.initialize(nvim, [])
        self.bufapps = {}
        logger.info('Initialized')

    @neovim.command('JupyterTestCommand', nargs="*", range=True)
    def testcommand(self, args, range):
        message = 'Command with args: {}, range: {}'.format(args, range)
        self.nvim.current.line = message
        logger.info(message)
        # self.zerorpc.print(message)

    @neovim.function('JupyterTestFunction', sync=True)
    def testsyncfunction(self, args):
        logger.info('test sync function: {}'.format(args))
        return args

    # allow_nested allows async functions to run when another sync function is being called
    # async function cannot return value
    @neovim.function('JupyterTestAsyncNestedFunction', sync=False)
    def testfunction(self, args):
        logger.info('test async nested function {}'.format(args))

    @neovim.command('JupyterStart')
    def start_child_app(self):
        ident = self.nvim.current.buffer.number
        bufapp = self.app.start_child_app(ident)
        bufapp.register_out_vim_buffer(self.nvim.current.buffer)
        self.bufapps[ident] = bufapp
        logger.info('Started child app %s', bufapp.connection_file)

    @neovim.shutdown_hook
    def shutdown_hook(self):
        logger.print('shuting down...')
