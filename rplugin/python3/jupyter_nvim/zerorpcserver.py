import zerorpc

class NvimRPC:
    def print(self, *args, **kwargs):
        print(*args, **kwargs)

    def print_dict(self, **kwargs):
        for key, val in kwargs.items():
            print(key, ':', val)


server = zerorpc.Server(NvimRPC())
server.bind("ipc:///tmp/jupyter-nvim")
server.run()
