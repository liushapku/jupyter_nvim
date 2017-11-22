import zerorpc
c = zerorpc.Client()
c.connect("ipc://jupyter-nvim")

c.print("a", "b")
