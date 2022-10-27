import argparse
import logging
import os
import pathlib
import shutil
import sys
import zipfile

from pyfiglet import Figlet

from input_validator.configuration import ConfigFromFile, ConfigFromString
from input_validator.data_validator import DataValidator
from input_validator.utils import write_errors_to_csv

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
    parser = argparse.ArgumentParser(description="validate Transantiago data.")

    parser.add_argument("path", help="Path for .zip data or list of paths", nargs="+")
    parser.add_argument("--parser", help="configuration json file to evaluate path")
    parser.add_argument(
        "--output",
        default=OUTPUT_NAME,
        help="path where report will be saved, if it is not provided we will use output path",
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )

    args = parser.parse_args(argv[1:])
    output_name = args.output
    configuration_file_content = args.parser
    is_path_list = len(args.path) > 1

    if is_path_list:
        input_path = args.path
    else:
        input_path = args.path[0]
        if zipfile.is_zipfile(input_path):
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                temporal_path = os.path.join(INPUTS_PATH, "tmp")
                zip_ref.extractall(temporal_path)
                input_path = os.path.join(temporal_path, zip_ref.namelist()[0].replace("/", ""))

    # date with file format
    date = pathlib.Path(args.path[0]).stem.replace("-", "")

    if configuration_file_content is None:
        config_obj = ConfigFromFile(CONFIG_PATH)
    else:
        configuration_file_content = configuration_file_content.replace('\'', '"')
        config_obj = ConfigFromString(configuration_file_content)
    data_validator = DataValidator(config_obj, input_path, date, logger=logger)

    if is_path_list:
        data_validator.start_iteration_over_path_list()
    else:
        data_validator.start_iteration_over_configuration_tree()

    # for success in validator.report:
    #    logger.info("{0} found in {1}".format(success[0], success[1]))
    if args.verbose:
        for key, value in data_validator.report_errors.items():
            logger.error(f"{key} contiene los siguientes errores:")
            for error in value:
                logger.error(error)

    file_path = os.path.join(OUTPUT_PATH, OUTPUT_NAME)
    write_errors_to_csv(file_path, data_validator)

    if not is_path_list:
        shutil.rmtree(os.path.join(INPUTS_PATH, "tmp"))
    logger.info(
        f"Archivos procesados, los resultados se encuentran en"
        f" {os.path.join(os.path.dirname(OUTPUT_PATH), output_name)}"
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv))
