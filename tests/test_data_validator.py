import json
import os
from unittest import TestCase

import mock

from data_validator import (
    DataValidator,
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

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_name(self, validate_node_rules):
        validate_node_rules.return_value = []
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(self.input_path, "configuration_check_name.json"),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual({}, data.report_errors)

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_name_error(self, validate_node_rules):
        validate_node_rules.return_value = []
        expected_errors = {
            "asd": [
                {
                    "message": "El nombre del directorio o archivo asd no se "
                    "encuentra en el directorio "
                    "{0}/.".format(self.data_path),
                    "title": "Nombre incorrecto",
                    "type": "formato",
                }
            ]
        }
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(
                self.input_path, "configuration_check_name_wrong_root.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_errors, data.report_errors)

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_rules_error(self, validate_node_rules):
        validate_node_rules.return_value = [{"error1", "error2"}]
        expected_errors = {
            "": [{"error1", "error2"}],
            "Diccionario": [{"error1", "error2"}],
            "Diccionario-Comunas.csv": [{"error1", "error2"}],
            "Diccionario-DetalleServicioZP_*_*.csv": [{"error1", "error2"}],
        }
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(self.input_path, "configuration_check_name.json"),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_errors, data.report_errors)

    def test_validate_nodes_rules_empty_case(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        path = self.data_path
        name = self.configuration_file["path"]["name"]
        rules = self.configuration_file["rules"]
        self.assertEqual([], data_validator.validate_node_rules(path, name, rules, ""))

    @mock.patch("data_validator.DataValidator.dispatch_rules")
    @mock.patch("data_validator.DataValidator.check_rules")
    def test_validate_nodes_rules_format_rule(self, check_rules, dispatch_rules):
        check_rules.return_value = []
        dispatch_rules.return_value = []
        data_validator = DataValidator(self.configuration_path, self.data_path)
        path = os.path.join(self.data_path, "Diccionario")
        name = self.configuration_file["children"][0]["children"][0]["path"]["name"]

        rules = self.configuration_file["children"][0]["children"][0]["rules"]
        header = ["ID", "NOMBRE"]
        self.assertEqual(
            [], data_validator.validate_node_rules(path, name, rules, header)
        )

    def test_dispatch_rules(self):
        data_validator = DataValidator(self.configuration_path, self.data_path)
        configuration_path = os.path.join(
            self.input_path, "configuration_dispatch.json"
        )
        with open(configuration_path) as json_config:
            configuration_file = json.loads(json_config.read())
            rules = configuration_file["children"][0]["children"][0]["rules"]
            header = ["ID", "COMUNA"]
            rules_dict = data_validator.dispatch_rules(rules, header)
            self.assertEqual(1, len(rules_dict["file"]))
            self.assertEqual(3, len(rules_dict["row"]))

    def test_check_rules_utf8(self):
        path = os.path.join(self.input_path, "utf8_data")
        latin1_name = "Diccionario-Servicios-Latin1.csv"
        header = [
            "ROUTE_ID",
            "ROUTE_NAME",
            "SERVICE_NA",
            "UN",
            "OP_NOC",
            "DIST",
            "PO_MOD",
            "SENTIDO",
            "COD_USUARI",
            "COD_TS",
            "COD_SINSER",
            "COD_SINRUT",
            "COD_USUSEN",
            "TIPO_SERV",
            "FREC_PM",
            "FREC_PT",
            "PLAZAS_PM",
            "PLAZAS_PT",
            "SEL_PM",
            "SEL_PT",
            "SEN1",
            "VALIDA",
        ]
        data_validator = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(self.input_path, "configuration_check_name.json"),
        )
        expected_error = [
            {
                "name": "Error de encoding",
                "type": "formato",
                "message": "El archivo Diccionario-Servicios-Latin1.csv no se encuentra en UTF-8.",
            }
        ]

        self.assertEqual(
            expected_error, data_validator.check_rules({}, path, latin1_name, header)
        )
        utf8_name = "Diccionario-Servicios-UTF-8.csv"
        self.assertEqual([], data_validator.check_rules({}, path, utf8_name, header))

    def test_check_rules_empty_row(self):
        path = os.path.join(self.input_path, "empty_row_data")
        empty_row_name = "Diccionario-Comunas-Empty-Row.csv"
        data_validator = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(self.input_path, "configuration_check_name.json"),
        )
        expected_error = [
            {
                "name": "Fila vacía",
                "type": "formato",
                "message": "El archivo posee una linea vacía en la fila 1.",
            }
        ]
        header = ["ID", "NOMBRE"]
        self.assertEqual(
            expected_error, data_validator.check_rules({}, path, empty_row_name, header)
        )

    def test_diccionario_comunas(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_comunas"),
            config_path=os.path.join(self.input_path, "configuration.json"),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
        ]
        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_comunas"),
            config_path=os.path.join(
                self.input_path, "configuration_diccionario_comunas_wrong.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-Comunas-Wrong.csv",
                "Diccionario/Diccionario-Comunas-Wrong.csv",
            ],
        ]

        expected_error_report = {
            "Diccionario-Comunas-Wrong.csv": [
                {
                    "name": "Valor duplicado",
                    "type": "formato",
                    "message": "La variable 0 está duplicada en la fila 2, columna ID.",
                },
                {
                    "name": "Valor duplicado",
                    "type": "formato",
                    "message": "La variable LAMPA está duplicada en la fila 2, columna NOMBRE.",
                },
            ]
        }
        self.assertEqual(expected_report, data.report)
        self.assertEqual(expected_error_report, data.report_errors)
