# -*- coding: utf8 -*-
import argparse
import logging
import os
import shutil
import sys
import zipfile

from pyfiglet import Figlet

from data_validator import DataValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
INPUTS_PATH = os.path.join(DIR_PATH, "input")
OUTPUT_PATH = os.path.join(DIR_PATH, "output")
OUTPUT_NAME = "transaccionesPorDia"
CONFIG_PATH = os.path.join(INPUTS_PATH, "configuration.json")


def main(argv):
    """
    Script to validate Transantiago Data
    """
    f = Figlet()
    logger.info(f.renderText("Input Validator"))

    # Arguments and description
    parser = argparse.ArgumentParser(description="validate Trasantiago data.")

    parser.add_argument("path", help="Path for .zip data or list of paths", nargs="+")
    parser.add_argument(
        "--output",
        default=None,
        help="path where report will be saved, if it is not provided we will use output path",
    )
    parser.add_argument("--path-list", help="Path is a path list.", action="store_true")
    args = parser.parse_args(argv[1:])
    is_path_list = args.path_list
    if is_path_list:
        input_path = args.path
    else:
        input_path = os.path.join(DIR_PATH, args.path[0])
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            temporal_path = os.path.join(INPUTS_PATH, "tmp")
            zip_ref.extractall(temporal_path)
            input_path = os.path.join(temporal_path, zip_ref.namelist()[0])

    validator = DataValidator(CONFIG_PATH, input_path, path_list=is_path_list)

    if is_path_list:
        validator.start_iteration_over_path_list()
    else:
        validator.start_iteration_over_configuration_tree()

    # output_path = args.output if args.output else OUTPUT_PATH

    for success in validator.report:
        logger.info("{0} found in {1}".format(success[0], success[1]))
    for key, value in validator.report_errors.items():
        logger.error("{0} contiene los siguientes errores:".format(key))
        for error in value:
            logger.error(error)

    if not is_path_list:
        shutil.rmtree(os.path.join(INPUTS_PATH, "tmp"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
