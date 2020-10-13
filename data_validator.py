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


def min_rows(count, row, n):
    """
    Check if a row has n columns as minimal
    :param: count: count of rows
    :param row: row to check
    :param n: min number of columns
    :return:
    """
    count += 1
    return count, count >= n


check_name_functions = {
    "name": check_name_file,
    "regex": check_regex_file,
    "root": lambda x, y: True,
}

# Funciones por ahora
# count -> se aplica en cada fila, se va contando y al final se retorna True o False según el conteo
# se puede hacer para el duplicado
# row -> se aplica a cada fila, cuando falla en una, se agrega al report
format_functions = {"min_rows": {"function": min_rows, "type": "count", "error": 2}}

file_errors = {
    1: {
        "name": "Nombre incorrecto",
        "type": "formato",
        "message": "El nombre del directorio o archivo no está en el formato correcto.",
    },
    2: {
        "name": "Número de filas menor al correcto",
        "type": "formato",
        "message": "El archivo posee menos filas de las que debería.",
    },
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
        """
        Start iteration over a configuration file
        """
        self.iterate_over_configuration_tree(self.config, "")

    def iterate_over_configuration_tree(self, node, path):
        """
        Iterate recursively a configuration file checking name format, path format and rules
        :param node: configuration node
        :param path: node path
        """

        # get variables
        name = node["path"]["name"]
        type_name = node["path"]["type"]
        new_path = os.path.join(path, name)
        absolute_path = os.path.join(self.data_path, path)
        rules = node["rules"]

        # check name and path format
        if check_name_functions[type_name](absolute_path, name):
            # if name correct check rules and report errors
            status = self.validate_node_rules(absolute_path, name, rules)
            for error in status:
                self.report_errors[name].append(error)
            # if not root case
            if name:
                self.report.append([name, new_path])

            # iterate over childs
            for child in node.get("children", []):
                self.iterate_over_configuration_tree(child, new_path)
        else:
            # report name and path errors
            self.report_errors[name].append(file_errors[1])

    def dispatch_rules(self, rules):
        """
        Split in diferent type of rules
        :param rules:
        :return: dict of rules
        """
        format_rules = rules.get("formatRules", [])
        semantic_rules = rules.get("semanticRules", [])
        rules_list = format_rules + semantic_rules
        rules_dict = defaultdict(list)
        for rule in rules_list:
            rule_name = rule["function"]
            rule_args = rule["args"]
            rule_type = format_functions[rule_name]["type"]
            rule_fun = format_functions[rule_name]["function"]
            rule_error = format_functions[rule_name]["error"]
            rules_dict[rule_type].append(
                {"fun": rule_fun, "args": rule_args, "error": rule_error}
            )

        return rules_dict

    def check_rules(self, rules_dict, path, name):
        return []

    def validate_node_rules(self, path, name, rules):
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules)
            report = self.check_rules(rules_dict, path, name)
        return report
