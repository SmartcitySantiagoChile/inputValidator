import os
from unittest import TestCase

from validators import RootValidator, NameValidator, RegexNameValidator


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
        validator = NameValidator(
            {"path": self.check_name_data_path, "name": "Diccionario"}
        )
        error_message = {
            "title": "Nombre incorrecto",
            "type": "formato",
            "message": "El nombre del directorio o archivo no está en el formato correcto.",
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
        validator = RegexNameValidator(
            {"path": path, "name": "Diccionario-DetalleServicioZP_*_*.csv"}
        )
        error_message = {
            "title": "No existe archivo con expresión regular",
            "type": "formato",
            "message": "No existe directorio o archivo con la expresión regular buscada.",
        }
        self.assertTrue(validator.apply())
        self.assertEqual("name", validator.get_fun_type())
        self.assertEqual(error_message, validator.get_error())

        # wrong case
        validator = RegexNameValidator({"path": path, "name": "wrong.csv"})
        self.assertFalse(validator.apply())
