
version_info = (0, 1, 0)
__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])

import os
import neovim
import logging
from jupyter_nvim.nvimapp import (
    JupyterNvimBufferApp,
    JupyterNvimApp,
)

@neovim.plugin
class JupyterNvimPlugin(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.app = JupyterNvimApp()
        self.log = self.app.log
        self.app.initialize(nvim, [])
        logger.info('Initialized')

    @neovim.command('JupyterStart', nargs="*", range=True)
    def start_child_app(self, args, range):
        bufno = self.nvim.current.buffer.number
        bufapp = self.app.start_child_app(bufno, [])
        bufapp.register_out_vim_buffer(self, bufno)
        self.log.info('child app %d started', bufno)
        # self.zerorpc.print(message)

    @neovim.command('JupyterExecute', nargs="*", range=False)
    def execute(self, args):
        self.log.info('JupyterExecute %s', args)
        # self.app('execute', )

    @neovim.shutdown_hook
    def shutdown_hook(self):
        logger.print('shuting down...')
