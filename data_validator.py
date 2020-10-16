import csv
import glob
import json
import os
from collections import defaultdict

from validators import NameValidator, RegexNameValidator, RootValidator


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
    "name": NameValidator,
    "regex": RegexNameValidator,
    "root": RootValidator,
}

# Funciones por ahora
# count -> se aplica en cada fila, se va contando y al final se retorna True o False según el conteo
# se puede hacer para el duplicado
# row -> se aplica a cada fila, cuando falla en una, se agrega al report
format_functions = {"min_rows": {"function": min_rows, "type": "count", "error": 2}}

file_errors = {
    2: {
        "name": "Número de filas menor al correcto",
        "type": "formato",
        "message": "El archivo posee menos filas de las que debería.",
    },
    3: {
        "name": "Archivo no es UTF-8",
        "type": "formato",
        "message": "El archivo no posee enconding UTF-8.",
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
        validator = check_name_functions[type_name](
            {"path": absolute_path, "name": name}
        )
        if validator.apply():
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
            self.report_errors[name].append(validator.get_error())

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
        """
        Check all rules over a csv file
        :param rules_dict: rules to check
        :param path: path of file
        :param name: name of file
        :return: report list with errors
        """
        report = []
        count_rules_list = rules_dict.get("count", [])
        # header_rules_list = rules_dict.get("header", [])
        # row_rules_list = rules_dict.get("row", [])
        count_rules = [
            {
                "count": 0,
                "fun": rule["fun"],
                "args": rule["args"],
                "error": rule["error"],
                "answer": False,
            }
            for rule in count_rules_list
        ]
        file = open(os.path.join(path, name), encoding="ASCII", errors="strict")
        csv_reader = csv.reader(file, delimiter=";")
        # header = next(csv_reader)
        next(csv_reader)  # TODO: delete
        # TODO: apply header rules
        for row in csv_reader:
            # TODO: apply row rules list
            # apply count rules
            for count_rule in count_rules:
                count_rule["count"], count_rule["answer"] = count_rule["fun"](
                    count_rule["count"], row, count_rule["args"]
                )
        file.close()
        # check all count rules errors
        for count_rule in count_rules:
            if not count_rule["answer"]:
                report.append(file_errors[count_rule["error"]])

        return report

    def validate_node_rules(self, path, name, rules):
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules)
            report = self.check_rules(rules_dict, path, name)
        return report
