import json


class ConfigFromFile:

    def __init__(self, file_path):
        with open(file_path, encoding="utf-8-SIG") as json_config:
            self.config = json.loads(json_config.read())

    def get_config(self):
        return self.config


class ConfigFromString:

    def __init__(self, configuration):
        self.config = json.loads(configuration)

    def get_config(self):
        return self.config
