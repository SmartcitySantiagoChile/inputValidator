import json

check_name_functions = {
    "name": lambda x: True,
    "regex": lambda x: True,
    "root": lambda x: True,
}


class DataIterator:
    """A class to iterate over a tree configuration json file"""

    def __init__(self, config_path, data_path, file_list=False):
        with open(config_path) as json_config:
            self.config = json.loads(json_config.read())
        self.data_path = data_path
        self.report = []

    def start_iteration_over_configuration_tree(self):
        self.iterate_over_configuration_tree(self.config)
        print(self.report)

    def iterate_over_configuration_tree(self, node):
        name = node["path"]["name"]
        type_name = node["path"]["type"]
        if check_name_functions[type_name](name):
            for child in node.get("children", []):
                self.iterate_over_configuration_tree(child)
        self.report.append(node["path"]["name"])
