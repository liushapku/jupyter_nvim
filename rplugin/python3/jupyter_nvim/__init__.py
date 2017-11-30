
version_info = (0, 1, 0)
__version__ = '.'.join(map(str, version_info[:3])) + ''.join(version_info[3:])

import os
import neovim
import logging
import argparse, io
import traceback
import shlex
from jupyter_nvim.nvimapp import (
    JupyterNvimBufferApp,
    JupyterNvimApp,
)

logger = logging.getLogger(__name__)
# if 'JUPYTER_NVIM_LOGFILE' in os.environ:
#     logfile = os.environ['NVIM_IPY_DEBUG_FILE'].strip()
#     logger.addHandler(logging.FileHandler(logfile, 'w'))
#     logger.level = logging.DEBUG

class HelpActionHandled(Exception):
    pass

class PrintHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        file = io.StringIO()
        parser.print_help(file=file)
        raise HelpActionHandled(file.getvalue())

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
        def add_help(parser):
            parser.add_argument('-h', '--help', action=PrintHelpAction, default=argparse.SUPPRESS,
                                help='show this help message and exit')

        self.parser = argparse.ArgumentParser(add_help=False)
        add_help(self.parser)
        subparsers = self.parser.add_subparsers()

        def add_parser(name, **kwargs):
            require_childid = kwargs.pop('require_childid', False)
            allow_unknown = kwargs.pop('allow_unknown', False)

            subparser = subparsers.add_parser(name, add_help=False, **kwargs)
            add_help(subparser)
            subparser.set_defaults(subcommand=name)

            def check_unknown(unknowns):
                if not allow_unknown and unknowns:
                    raise ValueError('Unknown options {}'.format(unknowns))
            subparser.set_defaults(check_unknown=check_unknown)

            if require_childid is not None:
                subparser.add_argument('-n', '--name', required=False, help='childid, child app identity', dest='childid')
            return subparser

        init = add_parser('init', help='initialize main app', require_childid=None)

        quit = add_parser('quit', help='quit main app', require_childid=None)
        quit.add_argument('childid', nargs='*', help='if has positional args, quit those child apps. Otherwise, quit all child apps')

        start = add_parser('start', help='start subapp', require_childid=True)
        start.add_argument('app_argv', nargs='*', help='argv for subapp')
        start.add_argument('--out', '-o', action='append', help='out buffer')
        start.add_argument('--inout', '--io', '-i', action='append', help='inout buffer')

        execute = add_parser('execute', help='execute code')
        execute.add_argument('code', nargs='+', help='code')

        run = add_parser('run', help='run code, specified by range')

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

    @neovim.function('Jupyter', sync=False)
    def main(self, raw_args):
        self.initialize()
        if isinstance(raw_args[0], dict):
            options = raw_args.pop(0)
        else:
            options = {}
        cbuf = self.nvim.current.buffer
        from_commandline = options.get('cmd', False)
        if from_commandline:
            cooked_args = []
            for arg in raw_args:
                cooked_args.extend(shlex.split(arg))
        else:
            cooked_args = raw_args

        self.log.info('%s: %s', options, cooked_args)

        try:
            args, unknown = self.parser.parse_known_args(cooked_args)
            args.check_unknown(unknown)
            if args.subcommand == 'init':
                pass
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
                    bufapp.register_out_buffer(cbuf.number)
                self.log.info('subapp started')
            elif args.subcommand == 'execute':
                code = '\n'.join(args.code)
                self.app('execute', code, args.childid)
                self.log.info('execute %s', code)
            elif args.subcommand == 'run':
                line1 = options.get('line1')
                line2 = options.get('line2')
                self.app('execute', '\n'.join(cbuf[line1-1:line2]))

        except HelpActionHandled as ex:
            self.echo(str(ex))
        except Exception as ex:
            buf = io.StringIO()
            traceback.print_exc(limit=None, file=buf)
            self.log.error('parse args error %s:\n%s', cooked_args, buf.getvalue())

    def echo(self, msg):
        self.nvim.vars['jupyter_nvim_msg'] = msg
        self.nvim.command('echo jupyter_nvim_msg')

    @neovim.shutdown_hook
    def shutdown_hook(self):
        self.quit()

    def quit(self):
        if self.app:
            self.app.quit()
            self.app = None
        self.log.info('quit app ...')
