
version_info = (0, 1, 0)
__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])

import os
import neovim
import logging
import argparse, io
import traceback
from jupyter_nvim.nvimapp import (
    JupyterNvimBufferApp,
    JupyterNvimApp,
)

logger = logging.getLogger(__name__)
# if 'JUPYTER_NVIM_LOGFILE' in os.environ:
#     logfile = os.environ['NVIM_IPY_DEBUG_FILE'].strip()
#     logger.addHandler(logging.FileHandler(logfile, 'w'))
#     logger.level = logging.DEBUG


@neovim.plugin
# @neovim.encoding(True)
class TestPlugin(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.app = None
        self.log = logger
        self.log.info('Plugin initialized')
        self._init_arg_parser()

    def _init_arg_parser(self):
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers()

        def add_parser(name, **kwargs):
            childid = kwargs.pop('need_childid', False)
            subparser = subparsers.add_parser(name, **kwargs)
            subparser.set_defaults(subcommand = name)

            # default: has --name but is not required
            if childid is None:
                pass
            elif childid is True:
                subparser.add_argument('--name', '--childid', '-n', required=True, help='childid, child app identity', dest='childid')
            elif childid is False:
                subparser.add_argument('--name', '--childid', '-n', required=False, help='childid, child app identity', dest='childid')

            return subparser

        init = add_parser('init', help='initialize main app', need_childid=None)

        quit = add_parser('quit', help='quit main app', need_childid=None)
        quit.add_argument('childid', nargs='*', help='if has positional args, quit those child apps. Otherwise, quit all child apps')

        start = add_parser('start', help='start subapp', need_childid=True)
        start.add_argument('app_argv', nargs='*', help='argv for subapp')
        start.add_argument('--out', '-o', action='append', help='out buffer')
        start.add_argument('--inout', '--io', '-i', action='append', help='inout buffer')

        execute = add_parser('execute', help='execute code')
        execute.add_argument('code', nargs='+', help='code')

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

    def initialize(self):
        if self.app is None:
            self.app = JupyterNvimApp()
            self.app.initialize(self.nvim, [])
            self.log = self.app.log
            self.log.info('App started')

    @neovim.command('Jupyter', nargs='+')
    def main(self, args):
        self.initialize()
        try:
            args, unknown = self.parser.parse_known_args(args)
            current = self.nvim.current.buffer.number
            if args.subcommand == 'init':
                assert not unknown, 'unknown options'
            elif args.subcommand == 'quit':
                if args.childid:
                    for childid in args.childid:
                        if childid in self.app:
                            self.app.quit_app(childid)
                            self.log.info('quit child app %s', childid)
                        else:
                            self.log.error('childid %s does not exist', childid)
                else:
                    self.quit()
                    self.log.info('quit all child apps and reset main app')
            elif args.subcommand == 'start':
                bufapp = self.app.start_child_app(args.childid, args.app_argv)
                has_buffer = False
                if args.out:
                    has_buffer = bufapp.register_out_buffer(*args.out) or has_buffer
                if args.inout:
                    has_buffer = bufapp.register_inout_buffer(*args.inout) or has_buffer
                if not has_buffer:
                    bufapp.register_out_buffer(current)
                self.log.info('subapp started')
            elif args.subcommand == 'execute':
                code = '\n'.join(args.code)
                self.app('execute', code, args.childid)
                self.log.info('execute %s', code)
        except BaseException as ex:
            buf = io.StringIO()
            traceback.print_exc(limit=None, file=buf)
            self.log.error('parse args error %s %s:\n%s', args, unknown, buf.getvalue())

    @neovim.shutdown_hook
    def shutdown_hook(self):
        self.shutdown()

    def quit(self):
        if self.app:
            self.app.quit()
            self.app = None
        self.log.info('shutting down...')
