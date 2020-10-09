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

    parser.add_argument("path", help="Path for .zip data")
    parser.add_argument(
        "--output",
        default=None,
        help="path where report will be saved, if it is not provided we will use output path",
    )
    args = parser.parse_args(argv[1:])
    input_path = os.path.join(DIR_PATH, args.path)
    # output_path = args.output if args.output else OUTPUT_PATH

    with zipfile.ZipFile(input_path, "r") as zip_ref:
        temporal_path = os.path.join(INPUTS_PATH, "tmp")
        zip_ref.extractall(temporal_path)
        input_path = os.path.join(temporal_path, zip_ref.namelist()[0])
        print(input_path)

    validator = DataValidator(CONFIG_PATH, input_path)
    validator.start_iteration_over_configuration_tree()

    for success in validator.report:
        logger.info("{0} found in {1}".format(success[0], success[1]))
    for key, value in validator.report_errors.items():
        logger.error("{0} contiene los siguientes errores:".format(key))
        for error in value:
            logger.error(error)

    shutil.rmtree(os.path.join(INPUTS_PATH, "tmp"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
