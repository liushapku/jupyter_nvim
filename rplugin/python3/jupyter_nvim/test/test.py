import jupyter_nvim
import jupyter_container.application as capp
import jupyter_container.kernelmanager as jkm
import jupyter_nvim.nvimapp as napp
from jupyter_client.multikernelmanager import MultiKernelManager
import sys
import threading
import time
from tornado import gen, ioloop



app = napp.JupyterNvimApp()
app.initialize([])
print(app.subcommand, app.subapp, app.generate_config)

# capp.JupyterContainerApp

# # owned bufapp
bufapp = bufapp0 = app.start_child_app(0, [])
print(bufapp)
print('connection file:', bufapp.connection_file)

# this bufapp.start does Nothing. The ioloop is started in ThreadedKernelClient.start_channels()
# each app has two threads, one for heartbeat, one fot other zmq channels
bufapp.start()
# msgid = bufapp.kernel_client.kernel_info()
# print(msgid)

# bufapp = bufapp1 = app.start_child_app(1, [])
# print(bufapp.childid, bufapp.connection_file)
# bufapp.start()


print('main thread:', threading.get_ident())
# ioloop.IOLoop.instance().start()
# time.sleep(10)

inputid = 0
while(True):
    inputid += 1
    code = input('In [{}]: '.format(inputid))
    bufapp.kernel_client.execute(code)
