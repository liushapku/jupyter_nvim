import jupyter_nvim
import jupyter_container.application as capp
import jupyter_container.kernelmanager as jkm
import jupyter_nvim.nvimapp as napp
from jupyter_client.multikernelmanager import MultiKernelManager
import sys
import threading
import time
from tornado import gen, ioloop
import neovim

nvim_socket = '/tmp/jupyter-nvim1'
nvim = neovim.attach('socket', path=nvim_socket)

app = napp.JupyterNvimApp()
app.initialize(nvim, [])
bufapp = app.start_child_app(1, ['-f=kernel-nvim-test.json'])
bufapp.register_out_vim_buffer(1, 2)


