import csv
import fnmatch
import json
import os
import sys
from collections import defaultdict

from input_validator.validators import (
    HeaderValidator,
    NotEmptyRowValidator,
    check_name_functions,
    file_functions,
)


class DataValidator:
    """A class to iterate over a tree configuration json file and validate data"""

    def __init__(self, config_path, data_path, date, path_list=False, logger=None):
        with open(config_path, encoding='utf-8-SIG') as json_config:
            self.config = json.loads(json_config.read())
        self.report_errors = defaultdict(list)
        self.report = []
        self.path_list = path_list
        self.data_path = data_path
        self.path_list_dict = []
        self.storage = {}
        self.log = logger
        self.temp_name = None
        self.files_checked = set()
        self.date = date

    def configuration_file_error(self, exception: Exception):
        """Send a file error message to the log and exit the program

        Args:
            exception: configuration file's exception
        """
        if self.log:
            self.log.error("Archivo de configuración mal formado")
            # self.log.error(exception)
        sys.exit("Procesamiento cancelado.")

    def configuration_fun_error(self, exception: Exception, fun_name: str):
        """Send a function's name error message to the log and exit the program.

        Args:
            exception: function's exception
            fun_name: function's name that throws the exception
        """
        if self.log:
            self.log.error("Nombre de función '{0}' no válida.".format(fun_name))
        self.configuration_file_error(exception)

    def configuration_args_error(self, exception: Exception, fun_name: str):
        """Send a function's args error message to the log and exit the program.

        Args:
            exception: function's exception
            fun_name: function's name that throws the exception
        """
        if self.log:
            self.log.error(
                "Error en la función {0}, problema con el argumento {1}".format(
                    fun_name.__class__.__name__, exception
                )
            )
        self.configuration_file_error(exception)

    def start_iteration_over_configuration_tree(self):
        """Start the iteration over a configuration file."""
        self.iterate_over_configuration_tree(self.config, "")

    def iterate_over_configuration_tree(self, node, path):
        """Iterate recursively a configuration file checking name format,
        path format, dependencies and validation rules.

        This method first check the node's dict keys. If there are valid,
        validate the dependencies.

        Args:
            node: configuration file's node to validate
            path: configuration file's path that contains the directory or
            files to validate
        """
        # get variables
        try:
            name = node["path"]["name"]
            type_name = node["path"]["type"]
            header = node["path"].get("header", "")
            absolute_path = os.path.join(self.data_path, path)
            dependencies = node["path"].get("dependencies", [])
            if type_name != "multi-regex":
                new_path = os.path.join(path, name)
            else:
                new_path = path
            rules = node["rules"]
        except KeyError as e:
            self.configuration_file_error(e)

        # check name and path format
        validator = check_name_functions[type_name](
            {"path": absolute_path, "name": name, "date": self.date}
        )
        # check dependencies
        missing_dependencies = []
        for dependency in dependencies:
            dependency_found = False
            for file in self.files_checked:
                if fnmatch.fnmatch(file, dependency):
                    dependency_found = True
            if not dependency_found:
                missing_dependencies.append(dependency)

        if validator.apply(self):
            # if name correct check rules and report errors
            if type_name == "regex" or type_name == "multi-regex" or type_name == "service_detail_regex":
                name = self.temp_name
                self.temp_name = None
            # check service detail error files
            if type_name == "service_detail_regex":
                self.report_error_by_validator(validator.args['names_with_incorrect_date'], validator)

            if missing_dependencies:
                for dependency in missing_dependencies:
                    error = {
                        "name": "Error de dependencias",
                        "type": "formato",
                        "message": f"El archivo {name} requiere el procesamiento del archivo con patrón {dependency}.",
                        "row": "",
                        "cols": "",
                    }
                    self.report_errors[name].append(error)
                return
            if rules:
                if type_name == "multi-regex":
                    status = self.validate_multi_node_rules(
                        absolute_path, name, rules, header
                    )
                elif type_name == "service_detail_regex":
                    status = []
                    for n in name:
                        status += self.validate_node_rules(absolute_path, n, rules, header)
                else:
                    status = self.validate_node_rules(
                        absolute_path, name, rules, header
                    )
                for error in status:
                    if isinstance(name, list):
                        for name_file in name:
                            self.report_errors[name_file].append(error)
                    else:
                        self.report_errors[name].append(error)
            # if not root case
            if name and new_path:
                self.report.append([name, new_path])

            # iterate over childs
            for child in node.get("children", []):
                self.iterate_over_configuration_tree(child, new_path)
        else:
            # report name and path errors
            self.report_error_by_validator(name, validator)

    def dispatch_rules(self, rules: dict, header: list, file_name: str) -> dict:
        """ Take the rules dict and split them by type

        Args:
            rules: rules dict
            header: file's header
            file_name: file name

        Returns:

        """
        format_rules = rules.get("formatRules", [])
        semantic_rules = rules.get("semanticRules", [])
        rules_list = format_rules + semantic_rules
        rules_dict = defaultdict(list)

        for rule in rules_list:
            rule_name = rule["function"]
            rule_args = {**rule["args"], **{"file_name": file_name}, "header": header}
            try:
                fun_object = file_functions[rule_name](rule_args)
            except KeyError as e:
                self.configuration_fun_error(e, rule_name)
            fun_type = fun_object.get_fun_type().name
            rules_dict[fun_type].append(fun_object)
        return rules_dict

    def check_rules(self, rules_dict, path, name, header) -> list:
        """
        Check all rules over a csv file
        :param rules_dict: rules to check
        :param path: file path
        :param name: file name
        :param header: file header
        :return: list
        """
        report = []
        files_rules_list = rules_dict.get("FILE", [])
        row_rules_list = rules_dict.get("ROW", [])
        storage_rule_list = rules_dict.get("STORAGE", [])
        for storage_fun in storage_rule_list:
            storage_fun.args["data_validator"] = self

        header_validator = HeaderValidator({"header": header})
        not_empty_row_validator = NotEmptyRowValidator({})

        # open file
        file = open(os.path.join(path, name), encoding="UTF-8-SIG", errors="strict")
        csv_reader = csv.reader(file, delimiter=";")
        if self.log:
            self.log.info("Procesando {0} ...".format(name))
        try:
            # check header
            if not header_validator.apply(next(csv_reader)):
                report.append(header_validator.get_error())
                file.close()
                return report

            # check rules
            for row in csv_reader:
                if not not_empty_row_validator.apply(row):
                    report.append(not_empty_row_validator.get_error())
                    continue

                # check row fun
                try:
                    for named_fun in row_rules_list:
                        if not named_fun.apply(row):
                            report.append(named_fun.get_error())
                    # apply file fun
                    for named_fun in files_rules_list:
                        named_fun.file_name = name
                        named_fun.apply(row)
                    # apply storage fun
                    for named_fun in storage_rule_list:
                        if not named_fun.apply(row):
                            report.append(named_fun.get_error())
                except Exception as e:
                    file.close()
                    self.configuration_args_error(e, named_fun)
        except UnicodeDecodeError:
            error = {
                "name": "Error de encoding",
                "type": "formato",
                "message": "El archivo {0} no se encuentra en UTF-8.".format(name),
                "row": "",
                "cols": "",
            }
            report.append(error)
        file.close()

        # check all file rules errors
        for file_fun in files_rules_list:
            if not file_fun.status:
                report.append(file_fun.get_error())

        # save file
        self.files_checked.add(name)
        return report

    def validate_node_rules(self, path, name, rules, header) -> list:
        """
        Validate node rules for a file
        :param path: file path
        :param name: file name
        :param rules: format and semantic rules
        :param header: file header
        :return:
        """
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules, header, name)
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

    def validate_multi_node_rules(self, path, name_list, rules, header):
        report = []
        if rules:
            rules_dict = self.dispatch_rules(rules, header, name_list)
            report = self.check_multiple_rules(rules_dict, path, name_list, header)

        return report

    def check_multiple_rules(self, rules_dict, path, name_list, header) -> list:
        # set variables
        offset = 4
        report = []
        files_rules_list = rules_dict.get("FILE", [])
        row_rules_list = rules_dict.get("ROW", [])
        storage_rule_list = rules_dict.get("STORAGE", [])
        multi_row_rules_list = rules_dict.get("MULTIROW", [])
        opened_files = []
        opened_csv_files = []

        # add self to storage fun
        for storage_fun in storage_rule_list:
            storage_fun.args["data_validator"] = self

        # set always validators
        header_validator = HeaderValidator({"header": header})
        not_empty_row_validator = NotEmptyRowValidator({})

        # open all files
        try:

            for name in name_list:
                # open file
                file = open(
                    os.path.join(path, name), encoding="UTF-8-SIG", errors="strict"
                )
                opened_files.append(file)
                csv_reader = csv.reader(file, delimiter=";")
                opened_csv_files.append(csv_reader)
                if self.log:
                    self.log.info("Procesando {0} ...".format(name))
                # skip offset
                for i in range(offset):
                    next(csv_reader)
            # check header
            for file_num in range(len(opened_files)):
                if not header_validator.apply(next(opened_csv_files[file_num])):
                    opened_files[file_num].close()
                    report.append(header_validator.get_error())
                    return report
        except UnicodeDecodeError:
            error = {
                "name": "Error de encoding",
                "type": "formato",
                "message": "El archivo {0} no se encuentra en UTF-8.".format(name),
                "row": "",
                "cols": "",
            }
            report.append(error)
            for file in opened_files:
                file.close()
            return report

        # check rules
        for csv_files in zip(*opened_csv_files):
            try:
                # apply multirow fun
                for named_fun in multi_row_rules_list:
                    named_fun.apply(csv_files)

                for row in csv_files:
                    if not not_empty_row_validator.apply(row):
                        report.append(not_empty_row_validator.get_error())
                        continue

                    # check row fun
                    try:
                        # apply file fun
                        for named_fun in files_rules_list:
                            named_fun.apply(row)

                        for named_fun in row_rules_list + storage_rule_list:
                            if not named_fun.apply(row):
                                report.append(named_fun.get_error())

                        # apply storage fun
                        for named_fun in storage_rule_list:
                            if not named_fun.apply(row):
                                report.append(named_fun.get_error())
                    except Exception as e:
                        opened_files[file_num].close()
                        self.configuration_args_error(e, named_fun)
            except UnicodeDecodeError:
                error = {
                    "name": "Error de encoding",
                    "type": "formato",
                    "message": "El archivo {0} no se encuentra en UTF-8.".format(name),
                    "row": "",
                    "cols": "",
                }
                report.append(error)
        for file in opened_files:
            file.close()

        return report

    def report_error_by_validator(self, name, validator):
        """
        report errors from validator
        Args:
            name:
            validator:
        """
        if isinstance(name, list):
            for n in name:
                self.report_errors[n].append(validator.get_error())
        else:
            self.report_errors[name].append(validator.get_error())
