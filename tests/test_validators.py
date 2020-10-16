import os
from unittest import TestCase

from validators import (
    RootValidator,
    NameValidator,
    RegexNameValidator,
    MinRowsValidator,
    ASCIIColValidator,
    DuplicateValueValidator,
)


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
        validator = ASCIIColValidator({"header": header, "col_index": 1})
        self.assertTrue(validator.apply(row))

        # Ñ case
        row = [0, "ÑUÑOA"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "name": "Valor contiene ñ o acentos",
            "type": "formato",
            "message": "La variable ÑUÑOA posee ñ o acentos en la fila 2, columna COMUNA.",
        }
        self.assertEqual(error_message, validator.get_error())

        # accent case
        row = [0, "Pucón"]
        self.assertFalse(validator.apply(row))
        error_message = {
            "name": "Valor contiene ñ o acentos",
            "type": "formato",
            "message": "La variable Pucón posee ñ o acentos en la fila 3, columna COMUNA.",
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
