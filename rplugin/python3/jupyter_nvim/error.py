
class IOLoopThread_WithErrorReport(IOLoopThread):
    def run(self):
        print('********* running')
        """Run my loop, ignoring EINTR events in the poller"""
        while True:
            try:
                self.ioloop.start()
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    print('>>>>>>>>>>>>>>>>>>>>>>> Error in thread', e)
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    print('>>>>>>>>>>>>>>>>>>>>>>> Error in thread', e)
                    raise
            else:
                break

class ThreadedKernelClient_WithErrorReport(ThreadedKernelClient):
    def start_channels(self, shell=True, iopub=True, stdin=True, hb=True):
        """Starts the channels for this kernel.

        This will create the channels if they do not exist and then start
        them (their activity runs in a thread). If port numbers of 0 are
        being used (random ports) then you must first call
        :meth:`start_kernel`. If the channels have been stopped and you
        call this, :class:`RuntimeError` will be raised.
        """
        self.ioloop_thread = IOLoopThread_WithErrorReport(self.ioloop)
        self.ioloop_thread.start()

        if shell:
            self.shell_channel._inspect = self._check_kernel_info_reply
            self.shell_channel.start()
            self.kernel_info()
        if iopub:
            self.iopub_channel.start()
        if stdin:
            self.stdin_channel.start()
            self.allow_stdin = True
        else:
            self.allow_stdin = False
        if hb:
            self.hb_channel.start()

class ThreadedIOLoopKernelManager_WithErrorReport(ThreadedIOLoopKernelManager):
    client_factory = ThreadedKernelClient_WithErrorReport

class ProxyMultiKernelManager_WithErrorReport(ProxyMultiKernelManager):
    kernel_manager_factory = ThreadedIOLoopKernelManager_WithErrorReport
