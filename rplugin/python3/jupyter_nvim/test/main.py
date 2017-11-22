#!/usr/bin/env python
# from jupyter_nvim import *
import jupyter_nvim
import jupyter_container.application as capp
import jupyter_container.kernelmanager as jkm
import jupyter_nvim.nvimapp as napp
from jupyter_client.multikernelmanager import MultiKernelManager
import sys

print('===')

reload(jupyter_nvim)
reload(capp)
reload(jkm)
reload(napp)

appc = capp.JupyterContainerApp()
appc.initialize([])

app = napp.JupyterNvimApp()
app.initialize([])

capp.JupyterContainerApp

# owned bufapp
bufapp = bufapp0 = app.start_child_app(0, [])
bufapp.connection_file
kc = bufapp.kernel_client
bufapp.iopub_port
bufapp.kernel_manager
bufapp.kernel_client
del bufapp

# connected bufapp
bufapp2 = app.start_child_app(1, ['--existing'])
bufapp2.connection_file
bufapp2.kernel_manager == None
bufapp2.kernel_client.shell_channel
del bufapp2

# connected bufapp
bufapp3 = app.start_child_app(2, ['--existing'])
bufapp3.connection_file
bufapp3.kernel_manager == None
bufapp3.kernel_client
del bufapp3

# multi kernel manager
mkm = app.kernel_manager
mkm.list_kernel_ids()
mkm.shutdown_all()
jkm.ProxyMultiKernelManager.kernel_manager_class.default_value
jkm.ProxyMultiKernelManager._default_kernel_manager_class(app.kernel_manager)



# directly test kernel manager
mm = jkm.ProxyMultiKernelManager()
mm.kernel_manager_class
mm.kernel_manager_factory
MultiKernelManager.default_kernel_name
kid = mm.start_kernel()
