import json
import os
import logging
from unittest import TestCase

import mock

from data_validator import (
    DataValidator,
)

logging.basicConfig(level=logging.CRITICAL)


class DataValidatorTest(TestCase):
    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.configuration_path = os.path.join(self.input_path, "configuration_files")
        self.data_path = os.path.join(self.input_path, "data")
        self.check_name_data_path = os.path.join(self.input_path, "check_name_data")
        with open(
            os.path.join(self.configuration_path, "configuration.json")
        ) as json_config:
            self.configuration_file = json.loads(json_config.read())

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_name(self, validate_node_rules):
        validate_node_rules.return_value = []
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(
                self.configuration_path, "configuration_check_name.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual({}, data.report_errors)

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_name_error(self, validate_node_rules):
        validate_node_rules.return_value = []
        expected_errors = {
            "asd": [
                {
                    "cols": "",
                    "message": "El nombre del directorio o archivo 'asd' no "
                    "se encuentra en el directorio "
                    "'/home/bastianleaf/PycharmProjects/inputValidator/tests/input/data/'.",
                    "row": "",
                    "title": "Nombre incorrecto",
                    "type": "formato",
                }
            ]
        }

        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(
                self.configuration_path, "configuration_check_name_wrong_root.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_errors, data.report_errors)

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_wrong_configuration(self, validate_node_rules):
        validate_node_rules.return_value = []
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(
                self.configuration_path, "configuration_wrong_file.json"
            ),
        )
        with self.assertRaises(SystemExit) as cm:
            data.start_iteration_over_configuration_tree()
            self.assertEqual(cm.exception, 1)

    def test_file_wrong_fun_name(self):
        logger = logging.getLogger(__name__)

        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_fun_name"),
            config_path=os.path.join(
                self.configuration_path, "configuration_wrong_fun_name.json"
            ),
            logger=logger,
        )
        with self.assertRaises(SystemExit) as cm:
            data.start_iteration_over_configuration_tree()
            self.assertEqual(cm.exception, 1)

    def test_file_wrong_fun_args(self):
        logger = logging.getLogger(__name__)
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_fun_name"),
            config_path=os.path.join(
                self.configuration_path, "configuration_wrong_fun_args.json"
            ),
            logger=logger,
        )
        with self.assertRaises(SystemExit) as cm:
            data.start_iteration_over_configuration_tree()
            self.assertEqual(cm.exception, 1)

    @mock.patch("data_validator.DataValidator.validate_node_rules")
    def test_file_iterator_rules_error(self, validate_node_rules):
        validate_node_rules.return_value = [{"error1", "error2"}]
        expected_errors = {
            "Diccionario-Comunas.csv": [{"error1", "error2"}],
        }
        data = DataValidator(
            data_path=self.data_path,
            config_path=os.path.join(
                self.configuration_path, "configuration_check_name.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_errors, data.report_errors)

    def test_validate_nodes_rules_empty_case(self):
        data_validator = DataValidator(
            os.path.join(self.configuration_path, "configuration.json"), self.data_path
        )
        path = self.data_path
        name = self.configuration_file["path"]["name"]
        rules = self.configuration_file["rules"]
        self.assertEqual([], data_validator.validate_node_rules(path, name, rules, ""))

    @mock.patch("data_validator.DataValidator.dispatch_rules")
    @mock.patch("data_validator.DataValidator.check_rules")
    def test_validate_nodes_rules_format_rule(self, check_rules, dispatch_rules):
        check_rules.return_value = []
        dispatch_rules.return_value = []
        data_validator = DataValidator(
            os.path.join(self.configuration_path, "configuration.json"), self.data_path
        )
        path = os.path.join(self.data_path, "Diccionario")
        name = self.configuration_file["children"][0]["children"][0]["path"]["name"]

        rules = self.configuration_file["children"][0]["children"][0]["rules"]
        header = ["ID", "NOMBRE"]
        self.assertEqual(
            [], data_validator.validate_node_rules(path, name, rules, header)
        )

    def test_dispatch_rules(self):
        data_validator = DataValidator(
            os.path.join(self.configuration_path, "configuration.json"), self.data_path
        )
        configuration_path = os.path.join(
            self.configuration_path, "configuration_dispatch.json"
        )
        with open(configuration_path) as json_config:
            configuration_file = json.loads(json_config.read())
            rules = configuration_file["children"][0]["children"][0]["rules"]
            header = ["ID", "COMUNA"]
            rules_dict = data_validator.dispatch_rules(rules, header)
            self.assertEqual(1, len(rules_dict["FILE"]))
            self.assertEqual(3, len(rules_dict["ROW"]))

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
            config_path=os.path.join(
                self.configuration_path, "configuration_check_name.json"
            ),
        )
        expected_error = [
            {
                "cols": "",
                "message": "El archivo Diccionario-Servicios-Latin1.csv no se encuentra en "
                "UTF-8.",
                "name": "Error de encoding",
                "row": "",
                "type": "formato",
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
            config_path=os.path.join(
                self.configuration_path, "configuration_check_name.json"
            ),
        )
        expected_error = [
            {
                "cols": "",
                "message": "El archivo posee una linea vacía en la fila 1.",
                "name": "Fila vacía",
                "row": 1,
                "type": "formato",
            }
        ]
        header = ["ID", "NOMBRE"]
        self.assertEqual(
            expected_error, data_validator.check_rules({}, path, empty_row_name, header)
        )

    def test_iterate_over_configuration_tree_path_list(self):
        path_list_data = os.path.join(self.input_path, "path_list_data")
        comunas_path = os.path.join(path_list_data, "Diccionario-Comunas.csv")
        estaciones_path = os.path.join(
            path_list_data, "Diccionario-EstacionesMetro.csv"
        )
        path_list = [comunas_path, estaciones_path]
        data = DataValidator(
            data_path=path_list,
            path_list=True,
            config_path=os.path.join(self.configuration_path, "configuration.json"),
        )
        data.start_iteration_over_path_list()
        expected_report = [
            ["Diccionario-Comunas.csv", path_list_data],
            ["Diccionario-EstacionesMetro.csv", path_list_data],
        ]
        self.assertEqual(expected_report, data.report)

    def test_get_path_list_nodes(self):
        path_list_data = os.path.join(self.input_path, "path_list_data")
        comunas_path = os.path.join(path_list_data, "Diccionario-Comunas.csv")
        estaciones_path = os.path.join(
            path_list_data, "Diccionario-EstacionesMetro.csv"
        )
        path_list = [comunas_path, estaciones_path]
        data = DataValidator(
            data_path=path_list,
            path_list=True,
            config_path=os.path.join(
                self.configuration_path, "configuration_path_list.json"
            ),
        )
        path_list_name = ["Diccionario-Comunas.csv", "Diccionario-EstacionesMetro.csv"]
        expected_dict = [
            {
                "path": {
                    "type": "name",
                    "name": "Diccionario-Comunas.csv",
                    "header": ["ID", "NOMBRE"],
                },
                "rules": {
                    "formatRules": [
                        {"function": "min_rows", "args": {"min": 42}},
                        {"function": "ascii", "args": {"col_index": 1}},
                        {"function": "duplicate", "args": {"col_index": 0}},
                        {"function": "duplicate", "args": {"col_index": 1}},
                    ],
                    "semanticRules": [],
                },
                "children": [],
            },
            {
                "path": {
                    "type": "name",
                    "name": "Diccionario-EstacionesMetro.csv",
                    "header": ["ID", "NOMBRE"],
                },
                "rules": {
                    "formatRules": [
                        {"function": "ascii", "args": {"col_index": 1}},
                        {"function": "duplicate", "args": {"col_index": 0}},
                        {"function": "duplicate", "args": {"col_index": 1}},
                    ],
                    "semanticRules": [],
                },
                "children": [],
            },
        ]

        data.create_path_dict(data.config, path_list_name)
        self.assertEqual(expected_dict, data.path_list_dict)

    def test_diccionario_comunas(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_comunas"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_comunas.json"
            ),
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
                self.configuration_path, "configuration_diccionario_comunas_wrong.json"
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
                    "cols": "ID",
                    "message": "La variable '0' "
                    "está duplicada en "
                    "la fila 2, columna "
                    "ID.",
                    "name": "Valor duplicado",
                    "row": 2,
                    "type": "formato",
                },
                {
                    "cols": "NOMBRE",
                    "message": "La variable "
                    "'LAMPA' está "
                    "duplicada en la "
                    "fila 2, columna "
                    "NOMBRE.",
                    "name": "Valor duplicado",
                    "row": 2,
                    "type": "formato",
                },
            ]
        }
        self.assertEqual(expected_report, data.report)
        self.assertEqual(expected_error_report, data.report_errors)

    def test_diccionario_servicios(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_servicios"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_servicios.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Servicios.csv", "Diccionario/Diccionario-Servicios.csv"],
        ]
        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_servicios"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_servicios_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()

        expected_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-Servicios-Wrong.csv",
                "Diccionario/Diccionario-Servicios-Wrong.csv",
            ],
        ]

        expected_report_error = {
            "Diccionario-Servicios-Wrong.csv": [
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'T207 00R' está "
                    "duplicada en la "
                    "fila 40, columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 40,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 414, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 414,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 418, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 418,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 580, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 580,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 585, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 585,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 1314, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 1314,
                    "type": "formato",
                },
                {
                    "cols": "COD_SINRUT",
                    "message": "La variable "
                    "'SCA' está "
                    "duplicada en la "
                    "fila 1405, "
                    "columna "
                    "COD_SINRUT.",
                    "name": "Valor duplicado",
                    "row": 1405,
                    "type": "formato",
                },
            ]
        }
        self.assertEqual(expected_report, data.report)
        self.assertEqual(expected_report_error, data.report_errors)

    def test_diccionario_patentes(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_patentes"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_patentes.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Patentes.csv", "Diccionario/Diccionario-Patentes.csv"],
        ]
        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_patentes"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_patentes_wrong.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-Patentes-Wrong.csv",
                "Diccionario/Diccionario-Patentes-Wrong.csv",
            ],
        ]

        expected_report_error = {
            "Diccionario-Patentes-Wrong.csv": [
                {
                    "cols": "",
                    "message": "El header no "
                    "corresponde al "
                    "archivo. Este "
                    "debe ser: "
                    "['FOLIO', 'UN', "
                    "'PLACA', "
                    "'PRIMERA', "
                    "'INGRESA', "
                    "'TIPO_FLOTA', "
                    "'MARCA', "
                    "'MODELO', "
                    "'MARCA_C', "
                    "'MODELO_C', "
                    "'AÑO', 'PLAZAS', "
                    "'TIPO_VEH', "
                    "'NORMA', "
                    "'Filtro_FAB_INC', "
                    "'Fecha_Instalación_Filtro_INC', "
                    "'Marca_Filtro_INC']",
                    "name": "Header incorrecto",
                    "row": "",
                    "type": "formato",
                }
            ]
        }
        self.assertEqual(expected_report, data.report)
        self.assertEqual(expected_report_error, data.report_errors)

    def test_diccionario_periodos_ts(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_periodos_ts"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_periodos_ts.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-PeriodosTS.csv", "Diccionario/Diccionario-PeriodosTS.csv"],
        ]
        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_periodos_ts"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_periodos_ts_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-PeriodosTS-Wrong.csv",
                "Diccionario/Diccionario-PeriodosTS-Wrong.csv",
            ],
        ]
        expected_error = {
            "Diccionario-PeriodosTS-Wrong.csv": [
                {
                    "cols": ["HORAFIN", "HORAINI"],
                    "message": "En la fila 1 el "
                    "valor de la "
                    "columna HORAFIN "
                    "es menor al "
                    "valor de la "
                    "columna "
                    "HORAINI.",
                    "name": "Inconsistencia " "entre valores",
                    "row": 1,
                    "type": "formato",
                }
            ]
        }
        self.assertEqual(expected_report, data.report)
        self.assertEqual(expected_error, data.report_errors)

    def test_shape_rutas(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_shape_rutas"),
            config_path=os.path.join(
                self.configuration_path, "configuration_shape_rutas.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Servicios.csv", "Diccionario/Diccionario-Servicios.csv"],
            ["Rutas", "Rutas"],
            ["ShapeRutas.csv", "Rutas/ShapeRutas.csv"],
        ]
        self.assertEqual(expected_data_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_shape_rutas"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_shape_rutas_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Servicios.csv", "Diccionario/Diccionario-Servicios.csv"],
            ["Rutas", "Rutas"],
            ["ShapeRutasWrong.csv", "Rutas/ShapeRutasWrong.csv"],
        ]
        self.assertEqual(expected_data_report, data.report)
        expected_errors = {
            "ShapeRutasWrong.csv": [
                {
                    "cols": "ROUTE_NAME",
                    "message": "La variable 'E06PRN' no se "
                    "encuentra en los valores "
                    "válidos para 'route_name' en "
                    "la fila 1, columna "
                    "ROUTE_NAME.",
                    "name": "El valor no es válido",
                    "row": 1,
                    "type": "valor",
                }
            ]
        }
        self.assertEqual(expected_errors, data.report_errors)

    def test_diccionario_zonificaciones(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_zonificaciones"),
            config_path=os.path.join(
                self.configuration_path, "configuration_diccionario_zonificaciones.json"
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
        ]

        self.assertEqual(expected_data_report, data.report)
        self.assertEqual({}, data.report_errors)
        # wrong case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_diccionario_zonificaciones"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_zonificaciones_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
        ]

        expected_error = {
            "Diccionario-Zonificaciones.csv": [
                {
                    "cols": ["X", "Y"],
                    "message": "Las coordenadas "
                    "'320439.3733', "
                    "'6299473.56' en "
                    "la fila 149819 no "
                    "se encuentran en "
                    "el rango "
                    "geográfico "
                    "correcto.",
                    "name": "Coordenadas " "inválidas",
                    "row": 149819,
                    "type": "valor",
                }
            ]
        }
        self.assertEqual(expected_data_report, data.report)
        self.assertEqual(expected_error, data.report_errors)

    def test_diccionario_estaciones_metro(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(
                self.input_path, "check_diccionario_estaciones_metro"
            ),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_estaciones_metro.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
            [
                "Diccionario-EstacionesMetro.csv",
                "Diccionario/Diccionario-EstacionesMetro.csv",
            ],
        ]

        self.assertEqual(expected_data_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(
                self.input_path, "check_diccionario_estaciones_metro"
            ),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_estaciones_metro_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_data_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
            [
                "Diccionario-EstacionesMetro.csv",
                "Diccionario/Diccionario-EstacionesMetro.csv",
            ],
        ]

        self.assertEqual(expected_data_report, data.report)
        expected_data_error = {
            "Diccionario-EstacionesMetro.csv": [
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 8, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 8,
                    "type": "formato",
                },
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 13, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 13,
                    "type": "formato",
                },
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 28, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 28,
                    "type": "formato",
                },
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 34, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 34,
                    "type": "formato",
                },
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 48, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 48,
                    "type": "formato",
                },
                {
                    "cols": ["LINEA"],
                    "message": "Existe un valor "
                    "incorrecto en la "
                    "fila 76, columna "
                    "LINEA. Los "
                    "valores solo "
                    "pueden ser "
                    "'['L1', 'L2', "
                    "'L3', 'L4', "
                    "'L4A', 'L5']'",
                    "name": "Valores incorrectos",
                    "row": 76,
                    "type": "formato",
                },
            ]
        }
        self.assertEqual(expected_data_error, data.report_errors)

    def test_diccionario_estaciones_metrotren(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(
                self.input_path, "check_diccionario_estaciones_metrotren"
            ),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_estaciones_metrotren.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
            [
                "Diccionario-EstacionesMetroTren.csv",
                "Diccionario/Diccionario-EstacionesMetroTren.csv",
            ],
        ]
        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

        # wrong case
        data = DataValidator(
            data_path=os.path.join(
                self.input_path, "check_diccionario_estaciones_metrotren"
            ),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_estaciones_metrotren_wrong.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_report, data.report)
        expected_data_error = {
            "Diccionario-EstacionesMetroTren.csv": [
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Alameda' no se encuentra en los valores válidos para 'communes' en la fila 1, columna CODIGOTRX.",
                    "row": 1,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Lo Valledor' no se encuentra en los valores válidos para 'communes' en la fila 2, columna CODIGOTRX.",
                    "row": 2,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Pedro Aguirre Cerda' no se encuentra en los valores válidos para 'communes' en la fila 3, columna CODIGOTRX.",
                    "row": 3,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Lo Espejo' no se encuentra en los valores válidos para 'communes' en la fila 4, columna CODIGOTRX.",
                    "row": 4,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Lo Blanco' no se encuentra en los valores válidos para 'communes' en la fila 5, columna CODIGOTRX.",
                    "row": 5,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Freire' no se encuentra en los valores válidos para 'communes' en la fila 6, columna CODIGOTRX.",
                    "row": 6,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion San Bernardo' no se encuentra en los valores válidos para 'communes' en la fila 7, columna CODIGOTRX.",
                    "row": 7,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Maestranza' no se encuentra en los valores válidos para 'communes' en la fila 8, columna CODIGOTRX.",
                    "row": 8,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Cinco Pinos' no se encuentra en los valores válidos para 'communes' en la fila 9, columna CODIGOTRX.",
                    "row": 9,
                    "cols": "CODIGOTRX",
                },
                {
                    "name": "El valor no es válido",
                    "type": "valor",
                    "message": "La variable 'Estacion Nos' no se encuentra en los valores válidos para 'communes' en la fila 10, columna CODIGOTRX.",
                    "row": 10,
                    "cols": "CODIGOTRX",
                },
            ]
        }
        self.assertEqual(expected_data_error, data.report_errors)

    def test_paraderos(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_paraderos"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_paraderos.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
            ["Paraderos", "Paraderos"],
            ["ConsolidadoParadas.csv", "Paraderos/ConsolidadoParadas.csv"],
        ]

        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)

    def test_diccionario_detalle_servicio(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(
                self.input_path, "check_diccionario_detalle_servicio"
            ),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_diccionario_detalle_servicio.json",
            ),
        )

        expected_report = [
            ["Diccionario", "Diccionario"],
            ["Diccionario-Comunas.csv", "Diccionario/Diccionario-Comunas.csv"],
            [
                "Diccionario-Zonificaciones.csv",
                "Diccionario/Diccionario-Zonificaciones.csv",
            ],
            [
                "Diccionario-DetalleServicioZP_20200627_20200731.csv",
                "Diccionario/Diccionario-DetalleServicioZP_*_*.csv",
            ],
        ]

        data.start_iteration_over_configuration_tree()
        self.assertEqual(expected_report, data.report)
        # self.assertEqual({}, data.report_errors)

    def test_frecuencias(self):
        # base case
        data = DataValidator(
            data_path=os.path.join(self.input_path, "check_frecuencias"),
            config_path=os.path.join(
                self.configuration_path,
                "configuration_frecuencias.json",
            ),
        )
        data.start_iteration_over_configuration_tree()
        expected_report = [
            ["Frecuencias", "Frecuencias"],
            [
                [
                    "Capacidades_PO20200627.csv",
                    "Distancias_PO20200627.csv",
                    "Frecuencias_PO20200627.csv",
                    "Velocidades_PO20200627.csv",
                ],
                "Frecuencias",
            ],
        ]

        self.assertEqual(expected_report, data.report)
        self.assertEqual({}, data.report_errors)
