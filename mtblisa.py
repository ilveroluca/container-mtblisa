#!/usr/bin/env python3

import os
import sys
import json
import shutil
import logging
import tempfile
from importlib import import_module
from parser_utils import maincommand, subcommand, arg

# isatools.io.mtbls module
_mtbls = None

# configure logger
logger = logging.getLogger()

""" list of valid formats """
VALID_FORMATS = ("isa-tab", "isa-json")

# set defaults
_DEFAULT_JSON_DATA_FILENAME = "data.json"


class NotValidIsaFormat(Exception):
    pass


def get_mtbls():
    # we need to load the mtbls module here to be able to properly initialize the logger
    global _mtbls
    #package_name = "isatools.net.mtbls" # Only for newer versions of ISA tools
    package_name = "isatools.io.mtbls"
    try:
        if _mtbls is None:
            _mtbls = import_module(package_name)
        return _mtbls
    except ImportError as e:
        raise RuntimeError("Could not import {} package. {}".format(package_name, e))


def _write_json(json_data, filename, output_path=None):
    if json_data is not None:
        if output_path is None:
            output_path = tempfile.mkdtemp()
        with open(os.path.join(output_path, filename), 'w') as outfile:
            json.dump(json_data, outfile, indent=4)
            logger.info("ISA-JSON written to: %s", os.path.join(output_path, filename))
    return output_path


def _write_output(source_path, target_path, output_filename, enable_compression):
    if source_path is not None:
        # create the target path if it doesnt exist
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        try:
            if enable_compression:
                # handle the archive creation
                os.chdir(target_path)
                tmp_file = tempfile.mktemp()
                shutil.make_archive(tmp_file, enable_compression, source_path)
                if output_filename:
                    shutil.move(".".join([tmp_file, enable_compression]), output_filename)
                logger.info("ISA-Tab written to %s/%s", target_path, output_filename)
            else:
                # move all files from the temp folder to the destination folder
                for f in os.listdir(source_path):
                    # remove existing files
                    destination = os.path.join(target_path, f)
                    if os.path.exists(destination):
                        if os.path.isfile(destination):
                            os.remove(destination)
                        else:
                            shutil.rmtree(destination)
                    # move actual file to its final destination
                    shutil.move(os.path.join(source_path, f), target_path)
                logger.info("Data written to %s", target_path)
        finally:
            # always remove the temporary folder
            shutil.rmtree(source_path)
    else:
        logger.warn("Source path '%s' is empty!!!", source_path)


def post(result, study, output_path, output_filename, enable_compression):
    if result:
        if output_filename is None:
            if enable_compression:
                output_filename = "{}.{}".format(study, enable_compression)
        _write_output(result, output_path, output_filename, enable_compression)


@maincommand(post=post, args=[
    arg("-v", "--verbosity", help="Verbosity level (default: ERROR)",
        default=logging.ERROR, choices=["INFO", "ERROR", "DEBUG", "WARN", "NOTSET"]),
    arg("-o", "--output-path", help="Output path (default = ./<StudyID>", default=None),
    arg("--output-filename", help="Output filename", default=None),
    arg("--enable-compression", choices=('zip', 'tar.gz'), help="Output format", default=None)])
def main_command(enable_compression, opts):
    """
    ISA slicer - a wrapper for isatools.io.mtbls
    """
    # configure logger
    logging.basicConfig(level=opts.verbosity)

    # initialize output-path
    if opts.output_path is None or opts.output_filename is not None and os.path.isabs(opts.output_filename):
        if opts.output_filename is not None:
            opts.output_path = os.path.dirname(opts.output_filename) or "."
        else:
            opts.output_path = os.path.join(".", opts.study) if "study" in opts else "."

    # make output_file always relative to the output_path
    if opts.output_filename is not None and os.path.isabs(opts.output_filename):
        opts.output_filename = os.path.basename(opts.output_filename)


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
        source_path = _write_json(get_mtbls().getj(study), "{}.json".format(study))

    return source_path


def _check_json_filename(study, output_filename, opts):
    if output_filename is None:
        opts.output_filename = "{}.json".format(study)


@subcommand(pre=_check_json_filename, args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1")
])
def get_factors(study, output_filename=_DEFAULT_JSON_DATA_FILENAME):
    """ Get factor names from a study. """
    factor_names = get_mtbls().get_factor_names(study)
    return _write_json(list(factor_names), output_filename)


@subcommand(pre=_check_json_filename, args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1"),
    arg("-q", "--query", help="A query like '--query \"Gender\"'")
])
def get_factor_values(study, query, output_filename=_DEFAULT_JSON_DATA_FILENAME):
    """ Get factor values """
    factor_values = get_mtbls().get_factor_values(study, query)
    return _write_json(list(factor_values), output_filename)


@subcommand(pre=_check_json_filename, args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1")
])
def get_summary(study, output_filename=_DEFAULT_JSON_DATA_FILENAME):
    """ Get variables summary from a study. """
    summary = get_mtbls().get_study_variable_summary(study)
    return _write_json(summary, output_filename)


@subcommand(pre=_check_json_filename, args=[
    arg("study", help="MetaboLights study ID, e.g. MTBLS1"),
    arg("-q", "--query", help="A query like '--query \"Gender\"'"),
    arg("-j", "--json-query", help="The path of the json containing the query")
])
def get_data_files(study, query=None, json_query=None, output_filename=_DEFAULT_JSON_DATA_FILENAME):
    """ Get data file references from a study (take care to ensure escaping of double quotes) """
    if query is None and json_query is not None:
        with open(query, encoding='utf-8') as query_fp:
            query = json.load(query_fp)
            logger.debug("running with query: %s", query)
    elif query is not None and json_query is not None:
        logger.warn("JSON query ignored")
    data_files = get_mtbls().get_data_files(study, query)
    logger.debug("Result data files list: %s", data_files)

    return _write_json(data_files, output_filename)


if __name__ == "__main__":
    try:
        main_command(sys.argv[1:])
    except Exception as e:
        logger.exception(e)
        logger.error(e)
        sys.exit(e.code if hasattr(e, "code") else 99)
