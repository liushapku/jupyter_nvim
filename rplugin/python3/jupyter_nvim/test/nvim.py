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

nvim_socket = '/tmp/nvimwbF3ai/0'
nvim = neovim.attach('socket', path=nvim_socket)

app = napp.JupyterNvimApp()
app.initialize(nvim, [])


