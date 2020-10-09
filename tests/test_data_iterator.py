import os
from unittest import TestCase

from data_validator import DataValidator, check_name_file, check_regex_file


class DataIteratorTest(TestCase):
    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.configuration_path = os.path.join(self.input_path, "configuration.json")
        self.data_path = os.path.join(self.input_path, "data")
        self.check_name_data_path = os.path.join(self.input_path, "check_name_data")

    def test_check_name_file_folder(self):
        self.assertTrue(check_name_file(self.check_name_data_path, "Diccionario"))

    def test_check_name_file_file(self):
        diccionario_comunas_folder = os.path.join(self.check_name_data_path, "")
        self.assertTrue(diccionario_comunas_folder, "Diccionario-Comunas.csv")

    def test_check_name_file_doesnt_exist(self):
        self.assertFalse(check_name_file(self.check_name_data_path, "Wrongname"))

    def test_check_regex_file(self):
        regex = "Diccionario-DetalleServicioZP_*_*.csv"
        self.assertTrue(
            check_regex_file(
                os.path.join(self.check_name_data_path, "Diccionario"), regex
            )
        )

    def test_check_regex_file_wrong(self):
        regex = "Diccionario*Detallel.csv"
        self.assertFalse(
            check_regex_file(
                os.path.join(self.check_name_data_path, "Diccionario"), regex
            )
        )

    def test_file_iterator(self):
        data = DataValidator(
            data_path=self.data_path, config_path=self.configuration_path
        )
        data.start_iteration_over_configuration_tree()
