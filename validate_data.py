# -*- coding: utf8 -*-
import argparse
import logging
import os
import sys

from pyfiglet import Figlet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
INPUTS_PATH = os.path.join(DIR_PATH, 'inputs')
OUTPUT_PATH = os.path.join(DIR_PATH, 'output')
OUTPUT_NAME = 'transaccionesPorDia'
CONFIG = os.path.join(INPUTS_PATH, 'configuration.json')


def main(argv):
    """
    Script to validate Transantiago Data
    """
    f = Figlet()
    logger.info(f.renderText('Input Validator'))

    # Arguments and description
    parser = argparse.ArgumentParser(description='validate Trasantiago data.')

    parser.add_argument('path', help='Path for .zip data')
    parser.add_argument('--output', default=None,
                        help='path where report will be saved, if it is not provided we will use output path')
    args = parser.parse_args(argv[1:])

    input_path = args.path
    output_path = args.output if args.output else OUTPUT_PATH
    print(CONFIG)




if __name__ == "__main__":
    sys.exit(main(sys.argv))
