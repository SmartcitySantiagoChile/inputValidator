# -*- coding: utf8 -*-
import argparse
import csv
import logging
import os
import shutil
import sys
import zipfile

from pyfiglet import Figlet

from data_validator import DataValidator

logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
INPUTS_PATH = os.path.join(DIR_PATH, "input")
OUTPUT_PATH = os.path.join(DIR_PATH, "output")
OUTPUT_NAME = "errores.csv"
CONFIG_PATH = os.path.join(INPUTS_PATH, "configuration.json")


def main(argv):
    """
    Script to validate Transantiago Data
    """
    logging.basicConfig(level=logging.INFO)

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
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )

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

    validator = DataValidator(
        CONFIG_PATH, input_path, path_list=is_path_list, logger=logger
    )

    if is_path_list:
        validator.start_iteration_over_path_list()
    else:
        validator.start_iteration_over_configuration_tree()

    output_path = args.output if args.output else OUTPUT_PATH

    # for success in validator.report:
    #    logger.info("{0} found in {1}".format(success[0], success[1]))
    if args.verbose:
        for key, value in validator.report_errors.items():
            logger.error("{0} contiene los siguientes errores:".format(key))
            for error in value:
                logger.error(error)
    with open(os.path.join(OUTPUT_PATH, OUTPUT_NAME), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Archivo", "Error", "Tipo", "Fila", "Columna(s)" "Detalle"])
        for key, value in validator.report_errors.items():
            for error in value:
                writer.writerow(
                    [
                        key,
                        error["name"],
                        error["type"],
                        error["row"],
                        error["cols"],
                        error["message"],
                    ]
                )

    if not is_path_list:
        shutil.rmtree(os.path.join(INPUTS_PATH, "tmp"))
    logger.info(
        "Archivos procesados, los resultados se encuentran en {0}".format(
            os.path.join(output_path, OUTPUT_NAME)
        )
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
