import inspect
import argparse


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


def maincommand(description=None, usage=None, args=None, exec_sub_command=True, pre=None, post=None):
    def decorator(func):
        main_parser = func.__globals__.get("__MAIN_PARSER__", None)
        if main_parser is None:
            main_parser = argparse.ArgumentParser(formatter_class=_CustomFormatter,
                                                  description=description or func.__doc__, usage=usage)
            for arg in args:
                main_parser.add_argument(*arg[0], **arg[1])
            sub_parsers = main_parser.add_subparsers(dest="command")
            func.__globals__["__MAIN_PARSER__"] = main_parser
            func.__globals__["__SUB_PARSERS__"] = sub_parsers

        def _inner_main(args):
            main_parser = func.__globals__.get("__MAIN_PARSER__", None)
            options = main_parser.parse_args(args)

            if pre:
                pre(**_get_cmd_options(options, pre))

            main_cmd_opts = _get_cmd_options(options, func)
            result = func(**main_cmd_opts)
            if exec_sub_command and "sub_command" in options:
                sub_cmd_opts = _get_cmd_options(options, options.sub_command)
                result = options.sub_command(**sub_cmd_opts)
            if post:
                post_args = _get_cmd_options(options, post)
                print("Post options %s " % post_args)
                post_args["result"] = result
                post(**post_args)

            return result

        return _inner_main

    return decorator


def subcommand(args=[], pre=None, post=None):
    def decorator(func):
        __SUB_PARSERS__ = func.__globals__["__SUB_PARSERS__"]
        if __SUB_PARSERS__ is None:
            raise RuntimeError("'maincommand' not defined!")
        parser = __SUB_PARSERS__.add_parser(func.__name__, description=func.__doc__, formatter_class=_CustomFormatter)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(sub_command=func)

    return decorator


def arg(*name_or_flags, **kwargs):
    return (name_or_flags, kwargs)
