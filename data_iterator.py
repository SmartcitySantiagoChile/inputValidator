import glob
import json
import os


def check_name_file(path, name):
    real_path = os.path.join(path, name)
    return os.path.exists(real_path)


def check_regex_file(path, regex):
    return True if len(glob.glob(os.path.join(path, regex))) > 0 else False


check_name_functions = {
    "name": check_name_file,
    "regex": lambda x, y: True,
    "root": lambda x, y: True,
}

file_errors = {
    1: {
        "name": "Nombre incorrecto",
        "type": "formato",
        "message": "El nombre del directorio o archivo no está en el formato correcto.",
    }
}


class DataIterator:
    """A class to iterate over a tree configuration json file"""

    def __init__(self, config_path, data_path, file_list=False):
        with open(config_path) as json_config:
            self.config = json.loads(json_config.read())
        self.data_path = data_path
        self.report_errors = []
        self.report = []

    def start_iteration_over_configuration_tree(self):
        self.iterate_over_configuration_tree(self.config, "")

    def iterate_over_configuration_tree(self, node, path):
        name = node["path"]["name"]
        type_name = node["path"]["type"]
        new_path = os.path.join(path, name)
        if check_name_functions[type_name](os.path.join(self.data_path, path), name):
            for child in node.get("children", []):
                self.iterate_over_configuration_tree(child, new_path)
        else:
            self.report_errors.append([new_path, file_errors[1]])
        if name:
            self.report.append(new_path)
