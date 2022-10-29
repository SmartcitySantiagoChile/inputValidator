import os
from unittest import TestCase

from input_validator.validators import (
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
    CheckColStorageValueValidator,
    BoundingBoxValueValidator,
    utm_to_wsg84,
    StoreColDictValues,
    CheckStoreColDictValuesValidator,
    CheckColStorageMultiValueValidator,
    FunType,
    RegexMultiNameValidator,
    FloatValueValidator,
    MultiRowColValueValidator,
    RegexServiceDetailNameValidator,
    CompareValueValidator,
    DateConsistencyValidator,
    CompleteYearFileConsistencyValidator,
)


class Dummy:
    def __init__(self):
        self.storage = {}


class ValidatorTest(TestCase):
    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.check_name_data_path = os.path.join(self.input_path, "check_name_data")


class MultiValidatorTest(ValidatorTest):
    def test_root_validator(self) -> None:
        validator = RootValidator({"path": self.check_name_data_path, "name": ""})
        error_message = {
            "cols": "",
            "message": "La raíz del directorio debe tener un nombre vacío en la "
            "configuración.",
            "row": "",
            "name": "Raíz incorrecta",
            "type": "formato",
        }
        self.assertTrue(validator.apply())
        self.assertEqual(FunType.NAME, validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

    def test_name_validator(self):
        # folder case
        args = {"path": self.check_name_data_path, "name": "Diccionario"}
        validator = NameValidator(args)
        error_message = {
            "cols": "",
            "message": "El nombre del directorio o archivo 'Diccionario' no se encuentra "
            "en el directorio "
            f"'{self.check_name_data_path}'.",
            "row": "",
            "name": "Nombre incorrecto",
            "type": "formato",
        }
        self.assertTrue(validator.apply())
        self.assertEqual(FunType.NAME, validator.get_fun_type())
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
        dummy_validator = Dummy()
        dummy_validator.temp_name = "test"
        args = {
            "path": path,
            "name": "Diccionario-DetalleServicioZP_*_*.csv",
            "date": "20200627",
        }
        validator = RegexNameValidator(args)

        error_message = {
            "cols": "",
            "message": "No existe directorio o archivo con la expresión regular "
            "'Diccionario-DetalleServicioZP_*_*.csv' en el directorio "
            f"'{path}' .",
            "row": "",
            "name": "No existe archivo con expresión regular",
            "type": "formato",
        }
        self.assertTrue(validator.apply(dummy_validator))
        self.assertEqual(FunType.NAME, validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

        # wrong case regex
        validator = RegexNameValidator(
            {"path": path, "name": "wrong.csv", "date": "20200627"}
        )
        self.assertFalse(validator.apply(dummy_validator))

        # wrong case date
        validator = RegexNameValidator(
            {
                "path": path,
                "name": "Diccionario-DetalleServicioZP_*_*.csv",
                "date": "20200127",
            }
        )
        error_message = {
            "name": "Fecha del archivo no corresponde con PO",
            "type": "formato",
            "message": "La fecha del archivo Diccionario-DetalleServicioZP_20200627_20200731.csv no "
            "corresponde a la fecha del programa PO '20200127'.",
            "row": "",
            "cols": "",
        }

        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(error_message, validator.get_error())

    def test_multi_regex_name_validator(self):
        # base case
        path = os.path.join(self.check_name_data_path, "Frecuencias")
        dummy_validator = Dummy()
        dummy_validator.temp_name = "test"
        args = {
            "path": path,
            "name": [
                "Capacidades_PO*.csv",
                "Distancias_PO*.csv",
                "Frecuencias_PO*.csv",
                "Velocidades_PO*.csv",
            ],
            "date": "20200627",
        }
        validator = RegexMultiNameValidator(args)

        expected_temporal_name = [
            "Capacidades_PO20200627.csv",
            "Distancias_PO20200627.csv",
            "Frecuencias_PO20200627.csv",
            "Velocidades_PO20200627.csv",
        ]

        expected_error = {
            "name": "No existen archivos con expresiones regulares",
            "type": "formato",
            "message": f"No existen directorios o archivos con la expresión regular '['Capacidades_PO*.csv', 'Distancias_PO*.csv', 'Frecuencias_PO*.csv', 'Velocidades_PO*.csv']' en el directorio '{path}' .",
            "row": "",
            "cols": "",
        }

        self.assertTrue(validator.apply(dummy_validator))
        self.assertEqual(expected_temporal_name, dummy_validator.temp_name)
        self.assertEqual(FunType.NAME, validator.get_fun_type())
        self.assertEqual(expected_error, validator.get_error())

        args = {
            "path": path,
            "name": [
                "Capacidades_PO*.csv",
                "Distancias_PO*.csv",
                "Frecuencias_PO*.csv",
                "Velocidades_PO*.csv",
            ],
            "date": "20200628",
        }
        expected_error = {
            "cols": "",
            "message": "La fecha de los archivos "
            "'Capacidades_PO20200627.csv,Distancias_PO20200627.csv,Frecuencias_PO20200627.csv,Velocidades_PO20200627.csv' "
            "no corresponde a la fecha del programa PO '20200628' .",
            "name": "Fecha de archivos no corresponde con PO",
            "row": "",
            "type": "formato",
        }
        validator = RegexMultiNameValidator(args)
        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(expected_error, validator.get_error())

        path = os.path.join(self.check_name_data_path, "Frecuencias2")
        args = {
            "path": path,
            "name": [
                "Capacidades_PO*.csv",
                "Distancias_PO*.csv",
                "Frecuencias_PO*.csv",
                "Velocidades_PO*.csv",
            ],
            "date": "20200627",
        }
        expected_error = {
            "cols": "",
            "message": "La fecha del archivo 'Capacidades_PO20200628.csv' no corresponde "
            "a la fecha del programa PO '20200627' .",
            "name": "Fecha de archivos no corresponde con PO",
            "row": "",
            "type": "formato",
        }
        validator = RegexMultiNameValidator(args)
        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(expected_error, validator.get_error())

    def test_min_rows_validator(self):
        # base case
        validator = MinRowsValidator({"min": 3})
        error_message = {
            "cols": "",
            "message": "El archivo posee 1 filas, cuando debería tener 3 filas como "
            "mínimo.",
            "name": "Número de filas menor al correcto",
            "row": "",
            "type": "formato",
        }
        self.assertFalse(validator.apply())
        self.assertEqual(error_message, validator.get_error())
        self.assertFalse(validator.apply())
        self.assertEqual(FunType.FILE, validator.get_fun_type())

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
            "cols": ["COMUNA"],
            "message": "La variable '['ÑUÑOA']' posee ñ o acentos en la fila 3 columna "
            "COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        # accent case
        row = [0, "Pucón"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "cols": ["COMUNA"],
            "message": "La variable '['Pucón']' posee ñ o acentos en la fila 4 columna "
            "COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "row": 4,
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        # multiple case
        validator = ASCIIColValidator({"header": header, "col_indexes": [0, 1]})
        row = ["Ñuñoa", "Pucón"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "cols": ["ID", "COMUNA"],
            "message": "Las variables '['Ñuñoa', 'Pucón']' poseen ñ o acentos en la fila "
            "2 columnas ID, COMUNA.",
            "name": "Valores contienen ñ o acentos",
            "row": 2,
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
            "cols": "ID",
            "message": "La variable '0' está duplicada en la fila 3, columna ID.",
            "name": "Valor duplicado",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

    def test_not_empty_row_validator(self):
        # base case
        row = ["0", "NUNOA"]
        validator = NotEmptyRowValidator({})
        self.assertTrue(validator.apply(row))

        # wrong case
        row = []
        self.assertFalse(validator.apply(row))
        error_message = {
            "cols": "",
            "message": "El archivo posee una linea vacía en la fila 3.",
            "name": "Fila vacía",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

    def test_header_validator(self):
        # base case
        header = ["ID", "COMUNA"]
        validator = HeaderValidator({"header": header})
        self.assertTrue(validator.apply(header))

        # wrong case
        header = ["COMUNA", "ID"]
        self.assertFalse(validator.apply(header))

        error_message = {
            "cols": "",
            "message": "El header no corresponde al archivo. Este debe ser: ['ID', "
            "'COMUNA']",
            "name": "Header incorrecto",
            "row": "",
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
        validator = NotEmptyValueValidator(
            {"header": header, "col_indexes": [1, 2], "conditions_to_ignore_row": []}
        )
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
            "cols": ["ROUTE_NAME"],
            "message": "Existe un valor vacío en la fila 3, columna ROUTE_NAME.",
            "name": "Valor vacío",
            "row": 3,
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
            "cols": ["ROUTE_NAME", "SERVICE_NA"],
            "message": "Existen valores vacíos en la fila 4, columnas ROUTE_NAME, "
            "SERVICE_NA.",
            "name": "Valor vacío",
            "row": 4,
            "type": "formato",
        }
        self.assertFalse(validator.apply(row))

        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
            "cols": ["SENTIDO"],
            "message": "Existe un valor incorrecto en la fila 3, columna SENTIDO. Los "
            "valores solo pueden ser '['I', 'R']'",
            "name": "Valores incorrectos",
            "row": 3,
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
            "cols": ["SENTIDO", "COD_USUARI"],
            "message": "Existen valores incorrectos en la fila 2, columnas SENTIDO, "
            "COD_USUARI. Los valores solo pueden ser '['I', 'R']'",
            "name": "Valores incorrectos",
            "row": 2,
            "type": "formato",
        }
        self.assertFalse(validator.apply(row))

        self.assertEqual(error_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
            "cols": "PLACA",
            "message": "La variable 'BXBXBX' no cumple con el formato AAAA11 o AA1111 en "
            "la fila 4, columna PLACA.",
            "name": "El valor no cumple con la expresión regular",
            "row": 4,
            "type": "formato",
        }

        self.assertEqual(expected_message, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
            "cols": ["PLAZAS"],
            "message": "Valor fuera de rango [11] en la fila 3, columna PLAZAS. Los "
            "valores solo pueden ser parte del rango [20, 200]",
            "name": "Valores fuera de rango",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(expected_message, validator.get_error())

        # empty case
        row = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ""]

        self.assertEqual(FunType.ROW, validator.get_fun_type())
        expected_message = {
            "cols": ["PLAZAS"],
            "message": "Valor fuera de rango [11] en la fila 3, columna PLAZAS. Los "
            "valores solo pueden ser parte del rango [20, 200]",
            "name": "Valores fuera de rango",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(expected_message, validator.get_error())
        self.assertFalse(validator.apply(row))

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
            "cols": ["HORAINI", "HORAFIN"],
            "message": "Existen valores en formato de hora incorrecto en la fila 3, "
            "columnas HORAINI, HORAFIN.",
            "name": "Formato de hora incorrecto",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(expected_error, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

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
            "cols": ["HORAFIN", "HORAINI"],
            "message": "En la fila 3 el valor de la columna HORAFIN es menor al valor de "
            "la columna HORAINI.",
            "name": "Inconsistencia entre valores",
            "row": 3,
            "type": "formato",
        }
        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.ROW, validator.get_fun_type())

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

        # wrong case
        row = ["1", "SANTIAGO"]
        validator.apply(row)
        expected_storage = ["NUNOA", "SANTIAGO"]
        self.assertEqual(expected_storage, dummy_object.storage["communes"])
        expected_error = {
            "cols": "",
            "message": "Error al almacenar valor",
            "name": "No se puede almacenar valor",
            "row": "",
            "type": "formato",
        }

        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.STORAGE, validator.get_fun_type())

    def test_check_col_storage_value(self):
        # base case
        dummy_object = Dummy()
        dummy_object.storage["route_name"] = ["201I", "430I"]
        header = ["ID", "ROUTE_NAME", "X-Coordinate", "Y-Coordinate"]

        validator = CheckColStorageValueValidator(
            {
                "header": header,
                "col_index": 1,
                "storage_name": "route_name",
                "data_validator": dummy_object,
            }
        )
        row = ["131985", "430I", "338029", "6306246"]
        self.assertTrue(validator.apply(row))

        # wrong case
        row = ["131985", "201R", "338029", "6306246"]
        self.assertFalse(validator.apply(row))
        expected_error = {
            "cols": "ROUTE_NAME",
            "message": "La variable '201R' no se encuentra en los valores válidos para "
            "'route_name' en la fila 3, columna ROUTE_NAME.",
            "name": "El valor no es válido",
            "row": 3,
            "type": "valor",
        }

        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.STORAGE, validator.get_fun_type())

    def test_bounding_box_value_validator(self):
        # base case
        header = ["ID", "ROUTE_NAME", "X-Coordinate", "Y-Coordinate"]
        validator = BoundingBoxValueValidator(
            {
                "header": header,
                "x_coordinate_index": 2,
                "y_coordinate_index": 3,
                "bounding_box": [
                    (-33.157966831331976, -70.92545685018858),
                    (-33.157966831331976, -70.40197466739595),
                    (-34.190746, -70.40197466739595),
                    (-34.190746, -70.92545685018858),
                ],
                "coordinate_system": "utm",
            }
        )
        row = ["131985", "430I", "338029", "6306246"]
        self.assertTrue(validator.apply(row))

        # wrong case
        row = ["131985", "430I", "28029", "1006246"]
        expected_error = {
            "cols": ["X-Coordinate", "Y-Coordinate"],
            "message": "Las coordenadas '28029.0', '1006246.0' en la fila 3 no se "
            "encuentran en el rango geográfico correcto.",
            "name": "Coordenadas inválidas",
            "row": 3,
            "type": "valor",
        }
        self.assertFalse(validator.apply(row))
        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.ROW, validator.get_fun_type())

    def test_utm_to_wsg84(self):
        test_case = [338029, 6306246]
        expected_res = (-33.37083676362541, -70.74108491315275)
        self.assertEqual(expected_res, utm_to_wsg84(*test_case))

    def test_store_col_dict_values(self):
        # base case
        header = ["ID_POLIGONO", "X", "Y", "NOMBRE_ZONA", "ID_ZONIFICACION"]
        dummy_object = Dummy()
        validator = StoreColDictValues(
            {
                "header": header,
                "key_index": 4,
                "value_indexes": [1, 2],
                "storage_name": "zone",
                "data_validator": dummy_object,
            }
        )
        row = ["0", "348541.1456", "6296986.971", "ORIENTE", "zonas_6"]
        validator.apply(row)
        expected_storage = {"zonas_6": [["348541.1456", "6296986.971"]]}
        self.assertEqual(expected_storage, dummy_object.storage["zone"])
        # wrong case
        row = ["582", "353790.8992", "6304293.784", "VITACURA", "eod_2006"]
        validator.apply(row)
        expected_storage = {
            "zonas_6": [["348541.1456", "6296986.971"]],
            "eod_2006": [["353790.8992", "6304293.784"]],
        }
        self.assertEqual(expected_storage, dummy_object.storage["zone"])
        expected_error = {
            "cols": "",
            "message": "Error al almacenar valor",
            "name": "No se puede almacenar valor",
            "row": "",
            "type": "formato",
        }

        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.STORAGE, validator.get_fun_type())

    def test_check_store_col_dict_values_validator(self):
        # base case
        dummy_object = Dummy()
        dummy_object.storage["zone"] = {
            "zonas_6": [
                ["348541.1456", "6296986.971"],
                ["348111.3295", "6298523.526"],
                ["349733.1474", "6292997.514"],
            ],
            "eod_2006": [["353790.8992", "6304293.784"]],
        }
        header = [
            "CODIGOTRX",
            "COMUNA",
            "LATITUD",
            "LONGITUD",
            "LINEA",
            "ESTANDAR",
            "TIPO",
            "ESTANDAR_ESTACION_UNICA",
            "CODIGO",
            "COLOR",
        ]

        validator = CheckStoreColDictValuesValidator(
            {
                "header": header,
                "key_name": "zonas_6",
                "value_indexes": [2, 3],
                "storage_name": "zone",
                "data_validator": dummy_object,
                "transform_data": "wsg84_to_utm",
            }
        )

        row = [
            "Agricola",
            "MACUL",
            "-33.491584",
            "-70.617529",
            "L5",
            "CAMINO AGRICOLA",
            "NORMAL",
            "CAMINO AGRICOLA",
            "AG",
            "V",
        ]

        self.assertTrue(validator.apply(row))

        dummy_object.storage["zone"] = {
            "zonas_6": [["-33.491584", "-70.617529"]],
            "eod_2006": [["353790.8992", "6304293.784"]],
        }
        header = [
            "CODIGOTRX",
            "COMUNA",
            "LATITUD",
            "LONGITUD",
            "LINEA",
            "ESTANDAR",
            "TIPO",
            "ESTANDAR_ESTACION_UNICA",
            "CODIGO",
            "COLOR",
        ]

        validator = CheckStoreColDictValuesValidator(
            {
                "header": header,
                "key_name": "zonas_6",
                "value_indexes": [2, 3],
                "storage_name": "zone",
                "data_validator": dummy_object,
                "transform_data": "none",
            }
        )

        row = [
            "Agricola",
            "MACUL",
            "-33.491584",
            "-70.617529",
            "L5",
            "CAMINO AGRICOLA",
            "NORMAL",
            "CAMINO AGRICOLA",
            "AG",
            "V",
        ]

        self.assertTrue(validator.apply(row))

        # wrong case
        dummy_object = Dummy()
        dummy_object.storage["zone"] = {
            "zonas_6": [["348541.1456", "6296986.971"], ["348111.3295", "6298523.526"]],
            "eod_2006": [["353790.8992", "6304293.784"]],
        }
        header = [
            "CODIGOTRX",
            "COMUNA",
            "LATITUD",
            "LONGITUD",
            "LINEA",
            "ESTANDAR",
            "TIPO",
            "ESTANDAR_ESTACION_UNICA",
            "CODIGO",
            "COLOR",
        ]

        validator = CheckStoreColDictValuesValidator(
            {
                "header": header,
                "key_name": "zonas_6",
                "value_indexes": [2, 3],
                "storage_name": "zone",
                "data_validator": dummy_object,
                "transform_data": "wsg84_to_utm",
            }
        )

        row = [
            "Agricola",
            "MACUL",
            "-33.491584",
            "-75.617529",
            "L5",
            "CAMINO AGRICOLA",
            "NORMAL",
            "CAMINO AGRICOLA",
            "AG",
            "V",
        ]

        self.assertFalse(validator.apply(row))

        expected_error = {
            "cols": ["LATITUD", "LONGITUD"],
            "message": "'['-33.491584', '-75.617529']' no se encuentran en los valores "
            "válidos para zonas_6 en la fila 2, columnas ['LATITUD', "
            "'LONGITUD'].",
            "name": "El valor no es válido",
            "row": 2,
            "type": "valor",
        }

        self.assertEqual(expected_error, validator.get_error())

        self.assertEqual(FunType.STORAGE, validator.get_fun_type())

    def test_check_col_storage_multi_value(self):
        # base case
        dummy_object = Dummy()
        dummy_object.storage["servicios"] = [
            "T556 00I",
            "T576 00I",
            "T576 03I",
            "T430 00I",
            "T430 C2 00I",
            "T406 C0 00I",
            "B51 00I",
            "B51 C0 00I",
        ]
        header = [
            "Código ZP",
            "Patente",
            "Código Parada TS_1",
            "Código Parada TS_2",
            "X",
            "Y",
            "Comuna",
            "Nombre Parada",
            "Mixta",
            "Unidades",
            "Servicios",
        ]

        validator = CheckColStorageMultiValueValidator(
            {
                "header": header,
                "col_index": 10,
                "storage_name": "servicios",
                "data_validator": dummy_object,
                "separator": "-",
            }
        )
        row = [
            "1",
            "RM-0045",
            "E-17-140-PO-7",
            "",
            "352880.2",
            "26301757.18",
            "LAS CONDES",
            "Parada 4 / (M) Escuela Militar",
            "SI",
            "U4-U6-U5",
            "T556 00I-T576 00I-T576 03I-T430 00I-T430 C2 00I-T406 C0 00I-B51 00I-B51 C0 00I",
        ]

        self.assertTrue(validator.apply(row))

        row = [
            "1",
            "RM-0045",
            "E-17-140-PO-7",
            "",
            "352880.2",
            "26301757.18",
            "LAS CONDES",
            "Parada 4 / (M) Escuela Militar",
            "SI",
            "U4-U6-U5",
            "B01 00I-T576 00I-T576 03I-T430 00I-T430 C2 00I-T406 C0 00I-B51 00I-B51 C0 00I",
        ]

        self.assertFalse(validator.apply(row))
        expected_error = {
            "cols": "Servicios",
            "message": "La variable '['B01 00I']' no se encuentra en los valores válidos "
            "para servicios en la fila 3, columna Servicios.",
            "name": "El valor no es válido",
            "row": 3,
            "type": "valor",
        }

        self.assertEqual(expected_error, validator.get_error())
        self.assertEqual(FunType.STORAGE, validator.get_fun_type())

    def test_float_value_validator(self):
        # base case
        header = [
            "Unidad de Negocio",
            "Código TS",
            "Código Usuario",
            "Sentido",
            "Tipo",
            "0:59",
            "5:29",
            "6:29",
            "7:59",
            "9:29",
            "12:29",
            "13:59",
            "16:29",
            "18:29",
            "20:29",
            "22:59",
            "23:59",
            "0:59",
            "5:29",
            "6:29",
            "10:59",
            "13:29",
            "17:29",
            "20:29",
            "22:59",
            "23:59",
            "0:59",
            "5:29",
            "9:29",
            "13:29",
            "17:29",
            "20:59",
            "22:59",
            "23:59",
        ]

        validator = FloatValueValidator(
            {
                "header": header,
                "col_indexes": [
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                ],
            }
        )
        row = [
            "2",
            "201",
            "201",
            "Ida",
            "",
            "0",
            "0",
            "736",
            "736",
            "674.6666667",
            "613.3333333",
            "613.3333333",
            "625.6",
            "736",
            "644",
            "0",
            "0",
            "0",
            "0",
            "460",
            "531.5555556",
            "588.8",
            "621",
            "613.3333333",
            "0",
            "0",
            "0",
            "0",
            "437",
            "529",
            "529",
            "473.1428571",
            "0",
            "0",
        ]

        self.assertTrue(validator.apply(row))

        # wrong case
        row = [
            "2",
            "201",
            "201",
            "Ida",
            "",
            "0",
            "0",
            "a",
            "736",
            "674.6666667",
            "613.3333333",
            "613.3333333",
            "625.6",
            "736",
            "644",
            "0",
            "0",
            "0",
            "0",
            "460",
            "531.5555556",
            "588.8",
            "621",
            "613.3333333",
            "0",
            "0",
            "0",
            "0",
            "437",
            "529",
            "529",
            "473.1428571",
            "0",
            "0",
        ]

        self.assertFalse(validator.apply(row))

        expected_error = {
            "name": "Formato float incorrecto",
            "type": "formato",
            "message": "Existe un valor en formato distinto a float en la fila 3, columna 6:29.",
            "row": 3,
            "cols": ["6:29"],
        }

        self.assertEqual(expected_error, validator.get_error())

        self.assertEqual(FunType.ROW, validator.get_fun_type())

    def test_multi_row_col_value_validator(self):
        # base case
        header = [
            "Unidad de Negocio",
            "Código TS",
            "Código Usuario",
            "Sentido",
            "Tipo",
            "0:59",
            "5:29",
            "6:29",
            "7:59",
            "9:29",
            "12:29",
            "13:59",
            "16:29",
            "18:29",
            "20:29",
            "22:59",
            "23:59",
            "0:59",
            "5:29",
            "6:29",
            "10:59",
            "13:29",
            "17:29",
            "20:29",
            "22:59",
            "23:59",
            "0:59",
            "5:29",
            "9:29",
            "13:29",
            "17:29",
            "20:59",
            "22:59",
            "23:59",
        ]

        validator = MultiRowColValueValidator(
            {
                "header": header,
                "col_indexes": [1, 2, 3],
                "file_names": ["archivo_1", "archivo_2"],
            }
        )
        row = [
            [
                "2",
                "201",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
            [
                "2",
                "201",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
            [
                "2",
                "201",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
        ]

        self.assertTrue(validator.apply(row))

        # wrong case
        row = [
            [
                "2",
                "201",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
            [
                "2",
                "201asda",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
            [
                "2",
                "201",
                "201",
                "Ida",
                "",
                "0",
                "0",
                "736",
                "736",
                "674.6666667",
                "613.3333333",
                "613.3333333",
                "625.6",
                "736",
                "644",
                "0",
                "0",
                "0",
                "0",
                "460",
                "531.5555556",
                "588.8",
                "621",
                "613.3333333",
                "0",
                "0",
                "0",
                "0",
                "437",
                "529",
                "529",
                "473.1428571",
                "0",
                "0",
            ],
        ]

        self.assertFalse(validator.apply(row))

        expected_error = {
            "name": "Valores distintos en archivos",
            "type": "valor",
            "message": "Existe un valor en distinto en los archivos ['archivo_1', 'archivo_2'] en la fila 3, columna Código TS.",
            "row": 3,
            "cols": ["Código TS"],
        }

        self.assertEqual(expected_error, validator.get_error())

        self.assertEqual(FunType.MULTIROW, validator.get_fun_type())

    def test_regex_service_detail_name_validator(self):
        path = os.path.join(self.check_name_data_path, "DiccionarioDosErrores")
        dummy_validator = Dummy()
        dummy_validator.temp_name = "test"
        args = {
            "path": path,
            "name": "Diccionario-DetalleServicioZP_*_*.csv",
            "date": "20210405",
        }
        validator = RegexServiceDetailNameValidator(args)

        error_message = {
            "cols": "",
            "message": "La fecha del archivo "
            "'Diccionario-DetalleServicioZP_20210301_20210315.csv' no "
            "corresponde al formato para la fecha del programa PO '20210405' ",
            "name": "Fecha de archivo incorrecta",
            "row": "",
            "type": "formato",
        }
        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(FunType.NAME, validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())
        error_message = {
            "cols": "",
            "message": "La fecha del archivo "
            "'Diccionario-DetalleServicioZP_20210415_20210430.csv' no "
            "corresponde al formato para la fecha del programa PO '20210405' ",
            "name": "Fecha de archivo incorrecta",
            "row": "",
            "type": "formato",
        }
        self.assertEqual(error_message, validator.get_error())

        # wrong case no date
        path = os.path.join(self.check_name_data_path, "DiccionarioVacío")
        args = {
            "path": path,
            "name": "Diccionario-DetalleServicioZP_*_*.csv",
            "date": "20210405",
        }
        validator = RegexServiceDetailNameValidator(args)

        error_message = {
            "cols": "",
            "message": "No existen directorios o archivos con la expresión regular "
            "'Diccionario-DetalleServicioZP_*_*.csv' en el directorio "
            f"'{path}",
            "name": "No existen archivos con expresiones regulares",
            "row": "",
            "type": "formato",
        }
        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(error_message, validator.get_error())

        # wrong case lower_date > upper_date
        path = os.path.join(self.check_name_data_path, "DiccionarioFechasInvertidas")
        args = {
            "path": path,
            "name": "Diccionario-DetalleServicioZP_*_*.csv",
            "date": "20210405",
        }
        validator = RegexServiceDetailNameValidator(args)

        error_message = {
            "cols": "",
            "message": "La fecha del archivo "
            "'Diccionario-DetalleServicioZP_20210430_20210416.csv' no "
            "corresponde al formato para la fecha del programa PO '20210405' ",
            "name": "Fecha de archivo incorrecta",
            "row": "",
            "type": "formato",
        }
        self.assertFalse(validator.apply(dummy_validator))
        self.assertEqual(error_message, validator.get_error())

        # wrong case lower_date > upper_date with correct dates first

        path = os.path.join(self.check_name_data_path, "DiccionarioFechasInvertidas2")
        args = {
            "path": path,
            "name": "Diccionario-DetalleServicioZP_*_*.csv",
            "date": "20210405",
        }
        validator = RegexServiceDetailNameValidator(args)

        error_message = {
            "cols": "",
            "message": "La fecha del archivo "
            "'Diccionario-DetalleServicioZP_20210502_20210515.csv' no "
            "corresponde al formato para la fecha del programa PO '20210405' ",
            "name": "Fecha de archivo incorrecta",
            "row": "",
            "type": "formato",
        }
        self.assertTrue(validator.apply(dummy_validator))
        self.assertEqual(error_message, validator.get_error())


class CompareValueValidatorTest(ValidatorTest):
    def setUp(self):
        header = ["Ano", "Mes", "Fecha", "Tipo_Dia", "Dia", "Observacion"]
        self.args = {
            "header": header,
            "col_indexes": [0, 2],
            "comparator": "year_in_date",
        }
        super().__init__()

    def test_correct_case(self):
        validator = CompareValueValidator(self.args)
        row = ["2007", "1", "2007-01-05", "LABORAL", "VIERNES"]
        self.assertTrue(validator.apply(row))

    def test_wrong_case(self):
        validator = CompareValueValidator(self.args)
        row = ["2006", "1", "2007-01-05", "LABORAL", "VIERNES"]
        self.assertFalse(validator.apply(row))
        expected_error = {
            "name": "Valor incorrecto",
            "type": "valor",
            "message": "Existen valores incorrectos en la fila 2, columnas Ano, Fecha,"
            " comparación incorrecta: 'año en fecha'.",
            "row": 2,
            "cols": ["Ano", "Fecha"],
        }

        self.assertEqual(validator.get_error(), expected_error)

    def test_compare_value_validator_year_is_in_date(self):
        self.assertFalse(CompareValueValidator.check_year_in_date("2020", "2021-01-20"))
        self.assertTrue(CompareValueValidator.check_year_in_date("2021", "2021-01-20"))

    def test_compare_value_validator_month_is_in_date(self):
        self.assertFalse(CompareValueValidator.check_month_in_date("2", "2021-01-20"))
        self.assertTrue(CompareValueValidator.check_month_in_date("1", "2021-01-20"))

    def test_compare_value_validator_day_name_is_in_date(self):
        self.assertFalse(
            CompareValueValidator.check_day_name_in_date("LUNES", "2021-01-20")
        )
        self.assertTrue(
            CompareValueValidator.check_day_name_in_date("MIERCOLES", "2021-01-20")
        )

    def test_fun_type(self):
        validator = CompareValueValidator(self.args)
        self.assertEqual(validator.get_fun_type(), FunType.ROW)


class DateConsistencyValidatorTest(ValidatorTest):
    def setUp(self):
        header = ["Ano", "Mes", "Fecha", "Tipo_Dia", "Dia", "Observacion"]
        self.args = {
            "header": header,
            "col_index": 2,
        }
        super().__init__()

    def test_date_consistency_validator(self):
        validator = DateConsistencyValidator(self.args)
        row = ["2007", "1", "2007-01-05", "LABORAL", "VIERNES"]
        self.assertTrue(validator.apply(row))
        row = ["2007", "1", "2007-01-06", "SABADO", "SABADO"]
        self.assertTrue(validator.apply(row))
        row = ["2007", "1", "2007-01-07", "DOMINGO", "DOMINGO"]
        self.assertTrue(validator.apply(row))

    def test_wrong_case(self):
        validator = DateConsistencyValidator(self.args)
        row = ["2007", "1", "2007-01-05", "LABORAL", "VIERNES"]
        self.assertTrue(validator.apply(row))
        row = ["2007", "1", "2007-01-05", "SABADO", "SABADO"]
        self.assertFalse(validator.apply(row))
        expected_error = {
            "cols": "Fecha",
            "message": "Fecha inconsistente en la fila 3, columna Fecha, fecha "
            "inconsistente respecto a la fecha anterior.",
            "name": "Fecha inconsistente",
            "row": 3,
            "type": "valor",
        }
        self.assertEqual(validator.get_error(), expected_error)

    def test_fun_type(self):
        validator = DateConsistencyValidator(self.args)
        self.assertEqual(validator.get_fun_type(), FunType.ROW)


class CompleteYearFileConsistencyValidatorTest(ValidatorTest):
    def setUp(self):
        header = ["Ano", "Mes", "Fecha", "Tipo_Dia", "Dia", "Observacion"]

        self.args = {
            "header": header,
            "col_index": 2,
            "file_name": "Diccionario_Tipo_Dia_20211230.csv",
        }
        super().__init__()

    def test_correct_case(self):
        validator = CompleteYearFileConsistencyValidator(self.args)
        rows = [
            ["2007", "1", "2021-12-30", "LABORAL", "VIERNES"],
            ["2007", "1", "2021-12-31", "SABADO", "SABADO"],
        ]
        for row in rows:
            validator.apply(row)

        self.assertTrue(validator.status)

    def test_wrong_case(self):
        validator = CompleteYearFileConsistencyValidator(self.args)
        rows = [
            ["2007", "1", "2021-12-29", "LABORAL", "JUEVES"],
            ["2007", "1", "2021-12-30", "LABORAL", "VIERNES"],
        ]
        for row in rows:
            validator.apply(row)
        self.assertFalse(validator.status)
        expected_error = {
            "name": "Fechas faltantes",
            "type": "formato",
            "message": "Fechas faltantes a partir de la fila 3, columna Fecha.",
            "row": 3,
            "cols": "Fecha",
        }
        self.assertEqual(expected_error, validator.get_error())

    def test_fun_type(self):
        validator = CompleteYearFileConsistencyValidator(self.args)
        self.assertEqual(validator.get_fun_type(), FunType.FILE)
