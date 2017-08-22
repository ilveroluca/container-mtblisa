import sys
import copy
import inspect
import argparse

__MAIN_COMMAND__ = {}
__SUB_COMMANDS__ = {}


class _CustomFormatter(argparse.RawTextHelpFormatter):
    """ Customize settings of the default RawTextHelpFormatter """

    def __init__(self, prog, indent_increment=2, max_help_position=100, width=None):
        super(_CustomFormatter, self).__init__(prog, indent_increment, max_help_position, width)


def _get_cmd_options(opts, func):
    spec = inspect.getargspec(func)
    res = {n: v for n, v in vars(opts).items() if n in spec.args}
    if "opts" in spec.args:
        res["opts"] = opts
    return res


def _get_subparsers(func):
    main_parser = func.__globals__["__MAIN_PARSER__"]
    if main_parser is None:
        raise RuntimeError("'maincommand' not defined! NOTICE: 'maincommand' must be defined before subcommands.")
    if "__SUB_PARSERS__" not in func.__globals__:
        sub_parsers = main_parser.add_subparsers(dest="command")
        func.__globals__["__SUB_PARSERS__"] = sub_parsers
    return func.__globals__["__SUB_PARSERS__"]


def maincommand(description=None, usage=None, args=None, exec_sub_command=True, pre=None, post=None):
    def decorator(func):
        global __MAIN_COMMAND__
        main_parser = func.__globals__.get("__MAIN_PARSER__", None)
        if main_parser is None:
            main_parser = argparse.ArgumentParser(formatter_class=_CustomFormatter,
                                                  description=description or func.__doc__, usage=usage)
            for arg in args:
                main_parser.add_argument(*arg[0], **arg[1])
            func.__globals__["__MAIN_PARSER__"] = main_parser

        def _inner_main(args=None):
            main_parser = func.__globals__.get("__MAIN_PARSER__", None)
            if args is None:
                args = sys.argv[1:]
            options = main_parser.parse_args(args)
            func.__globals__["__options__"] = options

            if pre:
                pre(**_get_cmd_options(options, pre))

            main_cmd_opts = _get_cmd_options(options, func)
            result = func(**main_cmd_opts)
            if exec_sub_command and "sub_command" in options:
                sub_cmd_opts = _get_cmd_options(options, options.sub_command)
                result = options.sub_command(**sub_cmd_opts)
            if post:
                post_args = _get_cmd_options(options, post)
                post_args["result"] = result
                post(**post_args)

            return result

        __MAIN_COMMAND__[func.__name__] = func
        return _inner_main

    return decorator


def subcommand(args=[], pre=None, post=None):
    def decorator(func):
        global __SUB_COMMANDS__
        __SUB_PARSERS__ = _get_subparsers(func)
        parser = __SUB_PARSERS__.add_parser(func.__name__, description=func.__doc__, formatter_class=_CustomFormatter)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])

        def inner_exec(args=None):
            if not "__options__" in func.__globals__:
                if args is None:
                    args = sys.argv[1:]
                main_parser = func.__globals__.get("__MAIN_PARSER__", None)
                options = main_parser.parse_args(args)
            else:
                options = func.__globals__["__options__"]

            if pre:
                pre(**_get_cmd_options(options, pre))
            cmd_opts = _get_cmd_options(options, func)
            result = func(**cmd_opts)
            if post:
                post_args = _get_cmd_options(options, post)
                post_args["result"] = result
                post(**post_args)

            return result

        parser.set_defaults(sub_command=inner_exec)
        __SUB_COMMANDS__[func.__name__] = inner_exec
        return inner_exec

    return decorator


def get_maincommand():
    global __MAIN_COMMAND__
    return copy.copy(__MAIN_COMMAND__)


def get_subcommands():
    global __SUB_COMMANDS__
    return copy.copy(__SUB_COMMANDS__)


def arg(*name_or_flags, **kwargs):
    return (name_or_flags, kwargs)
