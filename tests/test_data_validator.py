import json
import os
from unittest import TestCase

from data_validator import (
    DataValidator,
    min_rows,
    file_errors,
)


class DataValidatorTest(TestCase):
    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.configuration_path = os.path.join(self.input_path, "configuration.json")
        self.data_path = os.path.join(self.input_path, "data")
        self.check_name_data_path = os.path.join(self.input_path, "check_name_data")
        with open(self.configuration_path) as json_config:
            self.configuration_file = json.loads(json_config.read())

    def test_min_rows(self):
        self.assertEqual((2, True), min_rows(1, [], 1))
        self.assertEqual((2, False), min_rows(1, [], 3))

    def test_dispatch_rules(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        configuration_path = os.path.join(
            self.input_path, "configuration_dispatch.json"
        )
        with open(configuration_path) as json_config:
            configuration_file = json.loads(json_config.read())
            rules = configuration_file["children"][0]["children"][0]["rules"]
            expected_dict = {"count": [{"fun": min_rows, "args": 43, "error": 2}]}
            self.assertEqual(expected_dict, data_validator.dispatch_rules(rules))

    def test_check_rules_count_rules(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        rules_dict = {"count": [{"fun": min_rows, "args": 42, "error": 2}]}
        path = os.path.join(self.data_path, "Diccionario")
        name = "Diccionario-Comunas.csv"
        self.assertEqual([], data_validator.check_rules(rules_dict, path, name))

    def test_check_rules_count_rules_error(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        rules_dict = {"count": [{"fun": min_rows, "args": 45, "error": 2}]}
        path = os.path.join(self.data_path, "Diccionario")
        name = "Diccionario-Comunas.csv"
        expected_error = [file_errors[2]]
        self.assertEqual(
            expected_error, data_validator.check_rules(rules_dict, path, name)
        )

    def test_file_iterator_name(self):
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(self.input_path, "configuration_check_name.json"),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual({}, data.report_errors)

    def test_validate_nodes_rules_empty_case(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        path = self.data_path
        name = self.configuration_file["path"]["name"]
        rules = self.configuration_file["rules"]
        self.assertEqual([], data_validator.validate_node_rules(path, name, rules))

    def test_validate_nodes_rules_format_rule(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        path = self.data_path
        name = self.configuration_file["path"]["name"]
        rules = self.configuration_file["rules"]
        self.assertEqual([], data_validator.validate_node_rules(path, name, rules))
