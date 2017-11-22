import jupyter_nvim
import jupyter_container.application as capp
import jupyter_container.kernelmanager as jkm
import jupyter_nvim.nvimapp as napp
from jupyter_client.multikernelmanager import MultiKernelManager
import sys
from tornado import gen, ioloop
import ipdb



app = napp.JupyterNvimApp()
app.initialize([])
print(app.subcommand, app.subapp, app.generate_config)

# capp.JupyterContainerApp

# # owned bufapp
bufapp = bufapp0 = app.start_child_app(0, [])
print(bufapp)
print('connection file:', bufapp.connection_file)
# kc = bufapp.kernel_client
bufapp.start()
# kc.start()
# ipdb.set_trace()

# bufapp = bufapp1 = app.start_child_app(1, [])
# print(bufapp.childid, bufapp.connection_file)
# bufapp.start()

ioloop.IOLoop.instance().start()
