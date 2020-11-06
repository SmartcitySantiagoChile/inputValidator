import os
from unittest import TestCase

from validators import (
    RootValidator,
    NameValidator,
    RegexNameValidator,
    MinRowsValidator,
    ASCIIColValidator,
    DuplicateValueValidator,
    NotEmptyRowValidator,
    HeaderValidator,
    NotEmptyValueValidator,
    StringDomainValueValidator,
    RegexValueValidator,
    NumericRangeValueValidator,
    TimeValueValidator,
    GreaterThanValueValidator,
    StoreColValue,
)


class Dummy:
    def __init__(self):
        self.storage = {}


class DataValidatorTest(TestCase):
    def setUp(self) -> None:
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.check_name_data_path = os.path.join(self.input_path, "check_name_data")

    def test_root_validator(self) -> None:
        validator = RootValidator({"path": self.check_name_data_path, "name": ""})
        error_message = {
            "title": "Raiz incorrecta",
            "type": "formato",
            "message": "La raíz del directorio debe tener un nombre vacío en la configuración.",
        }
        self.assertTrue(validator.apply())
        self.assertEqual("name", validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

    def test_name_validator(self):
        # folder case
        args = {"path": self.check_name_data_path, "name": "Diccionario"}
        validator = NameValidator(args)
        error_message = {
            "title": "Nombre incorrecto",
            "type": "formato",
            "message": "El nombre del directorio o archivo {0} no se encuentra en el directorio {1}.".format(
                args["name"], args["path"]
            ),
        }
        self.assertTrue(validator.apply())
        self.assertEqual("name", validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

        # file case
        path = os.path.join(self.check_name_data_path, "Diccionario")
        validator = NameValidator({"path": path, "name": "Diccionario-Comunas.csv"})
        self.assertTrue(validator.apply())

        # wrong case
        validator = NameValidator({"path": path, "name": "wrong.csv"})
        self.assertFalse(validator.apply())

    def test_regex_name_validator(self):
        # base case
        path = os.path.join(self.check_name_data_path, "Diccionario")
        args = {"path": path, "name": "Diccionario-DetalleServicioZP_*_*.csv"}
        validator = RegexNameValidator(args)

        error_message = {
            "title": "No existe archivo con expresión regular",
            "type": "formato",
            "message": "No existe directorio o archivo con la expresión regular {0} en el directorio {1} .".format(
                args["name"], args["path"]
            ),
        }
        self.assertTrue(validator.apply())
        self.assertEqual("name", validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

        # wrong case
        validator = RegexNameValidator({"path": path, "name": "wrong.csv"})
        self.assertFalse(validator.apply())

    def test_min_rows_validator(self):
        # base case
        validator = MinRowsValidator({"min": 3})
        error_message = {
            "name": "Número de filas menor al correcto",
            "type": "formato",
            "message": "El archivo posee {0} filas, cuando debería tener {1} filas como mínimo".format(
                1, 3
            ),
        }
        self.assertFalse(validator.apply())
        self.assertEqual(error_message, validator.get_error())
        self.assertFalse(validator.apply())
        self.assertEqual("file", validator.get_fun_type())

        # get condition
        self.assertTrue(validator.apply())

    def test_ascci_col_validator(self):
        # base case
        row = ["0", "NUNOA"]
        header = ["ID", "COMUNA"]
        validator = ASCIIColValidator({"header": header, "col_indexes": [1]})
        self.assertTrue(validator.apply(row))

        # Ñ case
        row = [0, "ÑUÑOA"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "message": "La variable ['ÑUÑOA'] posee ñ o acentos en la fila 2 columna "
            "COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        # accent case
        row = [0, "Pucón"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "message": "La variable ['Pucón'] posee ñ o acentos en la fila 3 columna "
            "COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        # multiple case
        validator = ASCIIColValidator({"header": header, "col_indexes": [0, 1]})
        row = ["Ñuñoa", "Pucón"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "message": "Las variables ['Ñuñoa', 'Pucón'] poseen ñ o acentos en la fila 1 "
            "columnas ID, COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_duplicate_value_validator(self):
        # base case
        header = ["ID", "COMUNA"]
        row = ["0", "NUNOA"]
        validator = DuplicateValueValidator({"header": header, "col_index": 0})
        self.assertTrue(validator.apply(row))

        # wrong case
        row = ["0", "NUNOA"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "name": "Valor duplicado",
            "type": "formato",
            "message": "La variable 0 está duplicada en la fila 2, columna ID.",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_not_empty_row_validator(self):
        # base case
        row = ["0", "NUNOA"]
        validator = NotEmptyRowValidator({})
        self.assertTrue(validator.apply(row))

        # wrong case
        row = []
        self.assertFalse(validator.apply(row))
        error_message = {
            "name": "Fila vacía",
            "type": "formato",
            "message": "El archivo posee una linea vacía en la fila 2.",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_header_validator(self):
        # base case
        header = ["ID", "COMUNA"]
        validator = HeaderValidator({"header": header})
        self.assertTrue(validator.apply(header))

        # wrong case
        header = ["COMUNA", "ID"]
        self.assertFalse(validator.apply(header))

        error_message = {
            "name": "Header incorrecto",
            "type": "formato",
            "message": "El header no corresponde al archivo.",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_not_empty_value_validator(self):
        # base case
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
        validator = NotEmptyValueValidator({"header": header, "col_indexes": [1, 2]})
        self.assertTrue(validator.apply(header))

        # wrong case
        row = [
            "ROUTE_ID",
            "",
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

        self.assertFalse(validator.apply(row))

        error_message = {
            "message": "Existe un valor vacío en la fila 2, columna ROUTE_NAME.",
            "name": "Valor vacío",
            "type": "formato",
        }

        self.assertEqual(error_message, validator.get_error())

        row = [
            "ROUTE_ID",
            "",
            "",
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

        error_message = {
            "message": "Existen valores vacíos en la fila 3, columnas ROUTE_NAME, "
            "SERVICE_NA.",
            "name": "Valor vacío",
            "type": "formato",
        }
        self.assertFalse(validator.apply(row))

        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_string_domain_value_validator(self):
        # base case
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
        row = [
            "ROUTE_ID",
            "ROUTE_NAME",
            "SERVICE_NA",
            "UN",
            "OP_NOC",
            "DIST",
            "PO_MOD",
            "I",
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
        validator = StringDomainValueValidator(
            {"header": header, "col_indexes": [7], "domain": ["I", "R"]}
        )
        self.assertTrue(validator.apply(row))

        # wrong case
        row = [
            "ROUTE_ID",
            "",
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

        self.assertFalse(validator.apply(row))

        error_message = {
            "message": "Existe un valor incorrecto en la fila 2, columna SENTIDO. Los "
            "valores solo pueden ser ['I', 'R']",
            "name": "Valores incorrectos",
            "type": "formato",
        }

        self.assertEqual(error_message, validator.get_error())

        row = [
            "ROUTE_ID",
            "",
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

        validator = StringDomainValueValidator(
            {"header": header, "col_indexes": [7, 8], "domain": ["I", "R"]}
        )

        error_message = {
            "message": "Existen valores incorrectos en la fila 1, columnas SENTIDO, "
            "COD_USUARI. Los valores solo pueden ser ['I', 'R']",
            "name": "Valores incorrectos",
            "type": "formato",
        }
        self.assertFalse(validator.apply(row))

        self.assertEqual(error_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_regex_value_validator(self):
        # base case
        header = [
            "FOLIO",
            "UN",
            "PLACA",
            "PRIMERA",
            "INGRESA",
            "TIPO_FLOTA",
            "MARCA",
            "MODELO",
            "MARCA_C",
            "MODELO_C",
            "AÑO",
            "PLAZAS",
            "TIPO_VEH",
            "NORMA",
            "Filtro_FAB_INC",
            "Fecha_Instalación_Filtro_INC",
            "Marca_Filtro_INC",
        ]

        validator = RegexValueValidator(
            {
                "header": header,
                "col_index": 2,
                "regex": "^[A-Z]{4}[0-9]{2}|[A-Z]{2}[0-9]{4}$",
                "regex_name": "AAAA11 o AA1111",
            }
        )
        row = [0, 1, "BC1111"]
        self.assertTrue(validator.apply(row))

        row = [0, 1, "BCBC11"]
        self.assertTrue(validator.apply(row))

        # wrong case
        row = [0, 1, "BXBXBX"]
        self.assertFalse(validator.apply(row))

        expected_message = {
            "message": "La variable BXBXBX no cumple con el formato AAAA11 o AA1111 en la "
            "fila 3, columna PLACA.",
            "name": "El valor no cumple con la expresión regular",
            "type": "formato",
        }

        self.assertEqual(expected_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_numeric_domain_value_validator(self):
        # base case
        header = [
            "FOLIO",
            "UN",
            "PLACA",
            "PRIMERA",
            "INGRESA",
            "TIPO_FLOTA",
            "MARCA",
            "MODELO",
            "MARCA_C",
            "MODELO_C",
            "AÑO",
            "PLAZAS",
            "TIPO_VEH",
            "NORMA",
            "Filtro_FAB_INC",
            "Fecha_Instalación_Filtro_INC",
            "Marca_Filtro_INC",
        ]

        validator = NumericRangeValueValidator(
            {
                "header": header,
                "col_indexes": [11],
                "lower_bound": 20,
                "upper_bound": 200,
            }
        )
        row = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32]
        self.assertTrue(validator.apply(row))

        # wrong case
        row = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15]
        self.assertFalse(validator.apply(row))

        expected_message = {
            "message": "Valor fuera de rango [11] en la fila 2, columna PLAZAS. Los "
            "valores solo pueden ser parte del rango [20, 200]",
            "name": "Valores fuera de rango",
            "type": "formato",
        }
        self.assertEqual(expected_message, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_time_value_validator(self):
        # base case
        header = ["ID", "TIPODIA", "PERIODO", "HORAINI", "HORAFIN", "HORAS"]

        validator = TimeValueValidator(
            {
                "header": header,
                "col_indexes": [3, 4],
            }
        )
        row = ["30", "LABORAL", "01 - PRE NOCTURNO", "0:00:00", "0:59:59", "1"]

        self.assertTrue(validator.apply(row))

        # wrong case
        row = ["30", "LABORAL", "01 - PRE NOCTURNO", "30:00:00", "70:89:59", "1"]

        self.assertFalse(validator.apply(row))

        expected_error = {
            "name": "Formato de hora incorrecto",
            "type": "formato",
            "message": "Existen valores en formato de hora incorrecto en la fila 2, columnas HORAINI, HORAFIN.",
        }
        self.assertEqual(expected_error, validator.get_error())

        self.assertEqual("row", validator.get_fun_type())

    def test_greater_than_value_validator(self):
        # base case
        header = ["ID", "TIPODIA", "PERIODO", "HORAINI", "HORAFIN", "HORAS"]
        validator = GreaterThanValueValidator(
            {"header": header, "upper_col": 4, "lower_col": 3, "type": "time"}
        )
        row = ["30", "LABORAL", "01 - PRE NOCTURNO", "0:00:00", "0:59:59", "1"]
        self.assertTrue(validator.apply(row))

        # wrong case
        row = ["30", "LABORAL", "01 - PRE NOCTURNO", "1:00:00", "0:59:59", "1"]
        self.assertFalse(validator.apply(row))
        expected_error = {
            "name": "Inconsistencia entre valores",
            "type": "formato",
            "message": "En la fila 2 el valor de la columna HORAFIN es menor al valor de la columna HORAINI.",
        }
        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual("row", validator.get_fun_type())

    def test_store_col_value(self):
        # base case
        header = ["ID", "COMUNA"]
        dummy_object = Dummy()
        validator = StoreColValue(
            {
                "header": header,
                "col_index": 1,
                "storage_name": "communes",
                "data_validator": dummy_object,
            }
        )

        row = ["0", "NUNOA"]
        validator.apply(row)
        expected_storage = ["NUNOA"]
        self.assertEqual(expected_storage, dummy_object.storage["communes"])

        expected_error = {
            "name": "No se puede almacenar valor",
            "type": "formato",
            "message": "Error al almacenar valor",
        }

        self.assertEqual(expected_error, validator.get_error())
