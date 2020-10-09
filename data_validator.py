import glob
import json
import os
from collections import defaultdict


def check_name_file(path, name):
    """
    Check if file exists in path
    :param path: path to check
    :param name: file name
    :return: bool
    """
    real_path = os.path.join(path, name)
    return os.path.exists(real_path)


def check_regex_file(path, regex):
    """
    Check if regex file exists in path
    :param path: path to check
    :param regex: regular expression
    :return: bool
    """
    return True if len(glob.glob(os.path.join(path, regex))) > 0 else False


check_name_functions = {
    "name": check_name_file,
    "regex": check_regex_file,
    "root": lambda x, y: True,
}

file_errors = {
    1: {
        "name": "Nombre incorrecto",
        "type": "formato",
        "message": "El nombre del directorio o archivo no está en el formato correcto.",
    }
}


class DataValidator:
    """A class to iterate over a tree configuration json file and validate data"""

    def __init__(self, config_path, data_path, path_list=False):
        with open(config_path) as json_config:
            self.config = json.loads(json_config.read())
        self.report_errors = defaultdict(list)
        self.report = []
        if path_list:
            self.path_list = data_path
        else:
            self.data_path = data_path

    def start_iteration_over_configuration_tree(self):
        self.iterate_over_configuration_tree(self.config, "")

    def iterate_over_configuration_tree(self, node, path):
        name = node["path"]["name"]
        type_name = node["path"]["type"]
        new_path = os.path.join(path, name)
        if check_name_functions[type_name](os.path.join(self.data_path, path), name):
            if name:
                self.report.append([name, new_path])
            for child in node.get("children", []):
                self.iterate_over_configuration_tree(child, new_path)
        else:
            self.report_errors[name].append(file_errors[1])
