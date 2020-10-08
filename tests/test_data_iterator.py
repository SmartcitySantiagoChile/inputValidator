import os
from unittest import TestCase

from data_iterator import DataIterator


class DataIteratorTest(TestCase):
    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__))
        self.input_path = os.path.join(path, "input")
        self.configuration_path = os.path.join(self.input_path, "configuration.json")

    def test_file_iterator(self):
        file_list = os.path.join(
            os.path.join(self.input_path, "Original_2020-07 Julio"), "Diccionario"
        )
        file_list = os.path.join(file_list, "Diccionario-Comunas.csv")
        data = DataIterator(
            data_path=file_list, config_path=self.configuration_path, file_list=True
        )
        data.start_iteration_over_configuration_tree()
