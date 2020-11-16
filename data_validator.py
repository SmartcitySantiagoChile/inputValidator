import csv
import json
import os
from collections import defaultdict

from validators import (
    ASCIIColValidator,
    DuplicateValueValidator,
    GreaterThanValueValidator,
    HeaderValidator,
    MinRowsValidator,
    NameValidator,
    NotEmptyRowValidator,
    NotEmptyValueValidator,
    NumericRangeValueValidator,
    RegexNameValidator,
    RegexValueValidator,
    RootValidator,
    StoreColValue,
    StringDomainValueValidator,
    TimeValueValidator,
)

check_name_functions = {
    "name": NameValidator,
    "regex": RegexNameValidator,
    "root": RootValidator,
}

file_functions = {
    "min_rows": MinRowsValidator,
    "ascii": ASCIIColValidator,
    "duplicate": DuplicateValueValidator,
    "not_empty_row": NotEmptyRowValidator,
    "string_domain": StringDomainValueValidator,
    "regex_value": RegexValueValidator,
    "numeric_range": NumericRangeValueValidator,
    "greater_than": GreaterThanValueValidator,
    "time": TimeValueValidator,
    "not_empty_col": NotEmptyValueValidator,
    "store_col_value": StoreColValue,
}


class DataValidator:
    """A class to iterate over a tree configuration json file and validate data"""

    def __init__(self, config_path, data_path, path_list=False):
        with open(config_path) as json_config:
            self.config = json.loads(json_config.read())
        self.report_errors = defaultdict(list)
        self.report = []
        self.path_list = path_list
        self.data_path = data_path
        self.path_list_dict = []
        self.storage = {}

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
        header = node["path"].get("header", "")
        new_path = os.path.join(path, name)
        rules = node["rules"]
        absolute_path = os.path.join(self.data_path, path)
        # check name and path format
        validator = check_name_functions[type_name](
            {"path": absolute_path, "name": name}
        )
        if validator.apply():
            # if name correct check rules and report errors
            if rules:
                status = self.validate_node_rules(absolute_path, name, rules, header)
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

    def dispatch_rules(self, rules: dict, header: list) -> dict:
        """
        Split kind of rules
        :param rules:
        :param header:
        :return: dict of rules
        """
        format_rules = rules.get("formatRules", [])
        semantic_rules = rules.get("semanticRules", [])
        rules_list = format_rules + semantic_rules
        rules_dict = defaultdict(list)

        for rule in rules_list:
            rule_name = rule["function"]
            rule_args = rule["args"]
            rule_args["header"] = header
            fun_object = file_functions[rule_name](rule_args)
            fun_type = fun_object.get_fun_type()
            rules_dict[fun_type].append(fun_object)
        return rules_dict

    def check_rules(self, rules_dict, path, name, header):
        """
        Check all rules over a csv file
        :param rules_dict: rules to check
        :param path: file path
        :param name: file name
        :param header: file header
        :return: list
        """
        report = []
        files_rules_list = rules_dict.get("file", [])
        row_rules_list = rules_dict.get("row", [])
        storage_rule_list = rules_dict.get("storage", [])
        for storage_fun in storage_rule_list:
            storage_fun.args["data_validator"] = self

        header_validator = HeaderValidator({"header": header})
        not_empty_row_validator = NotEmptyRowValidator({})

        # open file
        file = open(os.path.join(path, name), encoding="UTF-8", errors="strict")
        csv_reader = csv.reader(file, delimiter=";")
        try:
            # check header
            if not header_validator.apply(next(csv_reader)):
                report.append(header_validator.get_error())
                file.close()
                report.append(header_validator.get_error())
                return report

            # check rules
            for row in csv_reader:
                if not not_empty_row_validator.apply(row):
                    report.append(not_empty_row_validator.get_error())
                    continue

                # check row fun
                for row_fun in row_rules_list:
                    if not row_fun.apply(row):
                        report.append(row_fun.get_error())

                # apply file fun
                for file_fun in files_rules_list:
                    file_fun.apply(row)

                # apply storage fun
                for storage_fun in storage_rule_list:
                    if not storage_fun.apply(row):
                        report.append(storage_fun.get_error())

        except UnicodeDecodeError:
            error = {
                "name": "Error de encoding",
                "type": "formato",
                "message": "El archivo {0} no se encuentra en UTF-8.".format(name),
            }
            report.append(error)
        file.close()

        # check all file rules errors
        for file_fun in files_rules_list:
            if not file_fun.status:
                report.append(file_fun.get_error())
        return report

    def validate_node_rules(self, path, name, rules, header):
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules, header)
            report = self.check_rules(rules_dict, path, name, header)
        return report

    def start_iteration_over_path_list(self):
        """
        Start iteration over a path list
        """
        path_list_names = []
        path_list_dict_name = {}
        for path in self.data_path:
            name = os.path.basename(path)
            path_list_names.append(name)
            path_list_dict_name[name] = os.path.dirname(path)

        self.create_path_dict(self.config, path_list_names)
        for node in self.path_list_dict:
            # get variable
            name = node["path"]["name"]
            absolute_path = path_list_dict_name[name]
            type_name = node["path"]["type"]
            header = node["path"].get("header", "")
            rules = node["rules"]
            # check name and path format
            validator = check_name_functions[type_name](
                {"path": absolute_path, "name": name}
            )
            if validator.apply():
                # if name correct check rules and report errors
                if rules:
                    status = self.validate_node_rules(
                        absolute_path, name, rules, header
                    )
                    for error in status:
                        self.report_errors[name].append(error)
                    # if not root case
                if name:
                    self.report.append([name, absolute_path])

            else:
                # report name and path errors
                self.report_errors[name].append(validator.get_error())

    def create_path_dict(self, node, name_list):
        """
        Iterate over path_dict and create
        :param node:
        :param name_list:
        """
        name = node["path"]["name"]
        if name in name_list:
            self.path_list_dict.append(node)
        for child in node["children"]:
            self.create_path_dict(child, name_list)
