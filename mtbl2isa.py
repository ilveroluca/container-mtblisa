#!/usr/bin/env python3

import os
import sys
import json
import shutil
import logging
import tempfile
from importlib import import_module
from parser_utils import maincommand, subcommand, arg

# FIXME: remove this temporary fix.
#        This is just to avoid some prints to the stderr stream
#        which cause that the Galaxy job is recognised as failed.
# sys.stderr = sys.stdout

# isatools.io.mtbls module
_mtbls = None

# configure logger
logger = logging.getLogger()

""" list of valid formats """
VALID_FORMATS = ("isa-tab", "isa-json")


class NotValidIsaFormat(Exception):
    pass


def get_mtbls():
    # we need to load the mtbls module here to be able to properly initialize the logger
    global _mtbls
    try:
        if _mtbls is None:
            _mtbls = import_module("isatools.io.mtbls")
        return _mtbls
    except ImportError as e:
        raise RuntimeError("Could not import isatools.io.mtbls package")


def _write_json(json_data, filename="data.json", output_path=None):
    if json_data is not None:
        if output_path is None:
            output_path = tempfile.mkdtemp()
        with open(os.path.join(output_path, filename), 'w') as outfile:
            json.dump(json_data, outfile, indent=4)
            logger.info("ISA-JSON written to: %s" % os.path.join(output_path, filename))
    return output_path


def _write_output(source_path, target_path, output_basename, enable_compression):
    if source_path is not None:
        logger.debug(os.listdir(source_path))

        if enable_compression:
            os.chdir(target_path)
            shutil.make_archive(output_basename, enable_compression, source_path)
            shutil.rmtree(source_path)
            logger.info("ISA-Tab written to %s.%s", output_basename, enable_compression)

        else:
            # 'outpath' is used as the 'extra_files_path' of the ISA composite dataset
            destination = os.path.join(target_path, output_basename) if target_path == "." else target_path
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.move(source_path, destination)
            logger.info("Dataset written to %s", destination)
    else:
        logger.warn("Source path '%s' is empty!!!", source_path)


def post(result, output_path, output_basename, enable_compression):
    if result:
        _write_output(result, output_path, output_basename, enable_compression)


@maincommand(post=post, args=[
    arg("--verbosity", help="Verbosity level (default: ERROR)",
        default=logging.ERROR, choices=["INFO", "ERROR", "DEBUG", "WARN", "NOTSET"]),
    arg("-o", "--output-path", help="Output path", default="."),
    arg("--output-basename", help="Output basename (e.g., study)", default=None),
    arg("--enable-compression", choices=('zip', 'tar.gz'), help="Output format", default=None)])
def main_command(output_basename, enable_compression, opts):
    """
    ISA slicer - a wrapper for isatools.io.mtbls
    """
    # configure logger
    logging.basicConfig(level=opts.verbosity)

    # initialize the output basename if not defined by CLI
    if opts.output_basename is None:
        if "study" in opts:
            opts.output_basename = opts.study
        else:
            opts.output_basename = "study"


@subcommand(args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1"),
    arg("-f", "--isa-format", choices=VALID_FORMATS, default=VALID_FORMATS[0],
        help="ISA dataset format, i.e., ISA-Tab or ISA-Json (default = {})".format(VALID_FORMATS[0])),
])
def get_study(study, isa_format=VALID_FORMATS[0]):
    """ Get a study as ISA format (either isa-tab or isa-json). """

    if isa_format not in VALID_FORMATS:
        raise NotValidIsaFormat("Invalid format %s" % isa_format)

    if isa_format == 'isa-tab':
        source_path = get_mtbls().get(study)
    elif isa_format == 'isa-json':
        source_path = _write_json(get_mtbls().getj(study))

    return source_path


@subcommand(args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1")
])
def get_factors(study):
    """ Get factor names from a study. """
    factor_names = get_mtbls().get_factor_names(study)
    return _write_json(list(factor_names))


@subcommand(args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1"),
    arg("-q", "--query", help="A query like '--query \"Gender\"'")
])
def get_factor_values(study, query):
    """ Get factor values """
    factor_values = get_mtbls().get_factor_values(study, query)
    return _write_json(list(factor_values))


@subcommand(args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1")
])
def get_summary(study):
    """ Get variables summary from a study. """
    MTBLS = _mtbls
    summary = MTBLS.get_study_variable_summary(study)
    return _write_json(summary)


@subcommand(args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1"),
    arg("-q", "--query", help="A query like '--query \"Gender\"'"),
    arg("-j", "--json-query", help="The path of the json containing the query")
])
def get_data_files(study, query=None, json_query=None):
    """ Get data file references from a study (take care to ensure escaping of double quotes) """
    if query is None and json_query is not None:
        with open(query, encoding='utf-8') as query_fp:
            query = json.load(query_fp)
            logger.debug("running with query: {}".format(query))
    elif query is not None and json_query is not None:
        logger.warn("JSON query ignored")
    data_files = get_mtbls().get_data_files(study, query)
    logger.debug("Result data files list: {}".format(data_files))

    return _write_json(data_files)


if __name__ == "__main__":
    try:
        main_command(sys.argv[1:])
    except Exception as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(e)
        else:
            logger.error(e.message)
        sys.exit(e.code if hasattr(e, "code") else 99)
