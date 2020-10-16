import json
import os
from collections import defaultdict

from validators import (
    ASCIIColValidator,
    DuplicateValueValidator,
    MinRowsValidator,
    NameValidator,
    RegexNameValidator,
    RootValidator,
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

    def dispatch_rules(self, rules: dict) -> dict:
        """
        Split kind of rules
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
            fun_object = file_functions[rule_name](rule_args)
            fun_type = fun_object.get_fun_type()
            rules_dict[fun_type].append(fun_object)
        return rules_dict

    def check_rules(self, rules_dict, path, name):
        """
        Check all rules over a csv file
        :param rules_dict: rules to check
        :param path: path of file
        :param name: name of file
        :return: report list with errors
        """
        report = [self.report]
        # count_rules_list = rules_dict.get("count", [])
        # # header_rules_list = rules_dict.get("header", [])
        # # row_rules_list = rules_dict.get("row", [])
        # count_rules = [
        #     {
        #         "count": 0,
        #         "fun": rule["fun"],
        #         "args": rule["args"],
        #         "error": rule["error"],
        #         "answer": False,
        #     }
        #     for rule in count_rules_list
        # ]
        # file = open(os.path.join(path, name), encoding="UTF-8", errors="strict")
        # csv_reader = csv.reader(file, delimiter=";")
        # # header = next(csv_reader)
        # next(csv_reader)  # TODO: delete
        # # TODO: apply header rules
        # for row in csv_reader:
        #     # TODO: apply row rules list
        #     # apply count rules
        #     for count_rule in count_rules:
        #         count_rule["count"], count_rule["answer"] = count_rule["fun"](
        #             count_rule["count"], row, count_rule["args"]
        #         )
        # file.close()
        # # check all count rules errors
        # for count_rule in count_rules:
        #     if not count_rule["answer"]:
        #         pass
        return report

    def validate_node_rules(self, path, name, rules):
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules)
            report = self.check_rules(rules_dict, path, name)
        return report
