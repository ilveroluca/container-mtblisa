#!/usr/bin/env python3

import os
import sys
import shutil
import logging
import unittest
import mtbl2isa
from parser_utils import get_subcommands, maincommand, arg

# create a logger instance
logger = logging.getLogger("test_logger")

# a valid study ID from the Metabolights database
_STUDY = "MTBLS331"


class TestsFunctions(unittest.TestCase):
    def _assert_not_empty_folder(self, result):
        self.assertIsNotNone(result, "Empty output path")
        self.assertTrue(os.path.isdir(result) > 0, "Output path is not a folder")
        self.assertTrue(len(os.listdir(result)) > 0, "Output path is empty")
        logger.debug("Output path: %s", result)

    def _assert_not_empty_json_data(self, result):
        # check result is not empty
        self._assert_not_empty_folder(result)
        # check the result path contains a valid json file
        self.assertTrue("data.json" in os.listdir(result),
                        "Output path {} doesn't contain the file 'data.json'".format(result))

    def _clean_output_folder(self, result):
        # remove the output path
        shutil.rmtree(result)
        self.assertFalse(os.path.exists(result), "Error when cleaning the output path")

    def test_list_of_subcommands(self):
        _SUB_COMMANDS = ["get_study", "get_factors", "get_factor_values", "get_summary", "get_data_files"]
        self.assertEqual(list(get_subcommands().keys()), _SUB_COMMANDS)

    def test_get_study(self):
        # check an invalid format
        self.assertRaises(mtbl2isa.NotValidIsaFormat, mtbl2isa.get_study, _STUDY, "another-format")
        # check all
        for _format in mtbl2isa.VALID_FORMATS:
            result = mtbl2isa.get_study(_STUDY, _format)
            self._assert_not_empty_folder(result)
            # cleaning
            self._clean_output_folder(result)

    def test_get_factors(self):
        result = mtbl2isa.get_factors(_STUDY)
        # check result is not empty
        self._assert_not_empty_json_data(result)
        # cleaning
        self._clean_output_folder(result)

    def test_get_factor_values_queries(self):
        queries = ("")  # TODO: add one or more queries
        for query in queries:
            result = mtbl2isa.get_factor_values(_STUDY, query)
            # check result is not empty
            self._assert_not_empty_json_data(result)
            # cleaning
            self._clean_output_folder(result)

    def test_get_summary(self):
        result = mtbl2isa.get_factors(_STUDY)
        # check result is not empty
        self._assert_not_empty_json_data(result)
        # cleaning
        self._clean_output_folder(result)

    def test_get_data_files_with_queries(self):
        queries = ("")  # TODO: add one or more queries
        for query in queries:
            result = mtbl2isa.get_data_files(_STUDY, query)
            # check result is not empty
            self._assert_not_empty_json_data(result)
            # cleaning
            self._clean_output_folder(result)

    def test_get_data_files_with_json_queries(self):
        jqueries = ("")  # TODO: add one or more queries
        for jquery in jqueries:
            result = mtbl2isa.get_data_files(_STUDY, json_query=jquery)
            # check result is not empty
            self._assert_not_empty_json_data(result)
            # cleaning
            self._clean_output_folder(result)


@maincommand(args=[
    arg("--verbosity", help="Test verbosity level (default = 2)", default=2, choices=[0, 1, 2]),
    arg("--global-log-level", help="Global logs verbosity level (default: ERROR)",
        default=logging.ERROR, choices=["INFO", "ERROR", "DEBUG", "WARN", "NOTSET"]),
    arg("--test-log-level", help="Test logs verbosity level (default: NOTSET)",
        default=logging.ERROR, choices=["INFO", "ERROR", "DEBUG", "WARN", "NOTSET"]),
    arg("-s", "--study", help="StudyID used for running the test suite (default: {0})".format(_STUDY), default=_STUDY)])
def run_tests(study, verbosity, test_log_level, global_log_level):
    # configure logs
    logging.basicConfig(level=global_log_level)
    logger.setLevel(test_log_level)
    # set the study
    _STUDY = study
    logger.info("Using %s as study for running the test suite!!!", _STUDY)
    # configure and run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestsFunctions)
    unittest.TextTestRunner(verbosity=verbosity).run(suite)


if __name__ == '__main__':
    # run tests
    run_tests(sys.argv[1:])
    mtbl2isa.maincommand(exec_sub_command=False)
