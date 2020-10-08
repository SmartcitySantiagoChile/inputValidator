import json


class DataIterator:
    """A class to iterate over a tree configuration json file"""

    def __init__(self, config_path, data_path, file_list=False):
        with open(config_path) as json_config:
            self.config = json.loads(json_config.read())
        self.data_path = data_path

    def iterate_over_configuration_tree(self):
        print(self.config)
