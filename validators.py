import glob
import os
from abc import ABCMeta, abstractmethod


class Validator(object, metaclass=ABCMeta):
    def __init__(self, args):
        self.args = args
        super().__init__()

    @abstractmethod
    def apply(self):
        pass

    @abstractmethod
    def get_error(self):
        pass

    @abstractmethod
    def get_fun_type(self):
        pass


class RootValidator(Validator):
    def apply(self):
        return True

    def get_error(self):
        pass

    def get_fun_type(self):
        return "name"


class NameValidator(Validator):
    def apply(self):
        """
        Check if file exists in path
        :return:
        """
        path = self.args["path"]
        name = self.args["name"]
        real_path = os.path.join(path, name)
        return os.path.exists(real_path)

    def get_error(self):
        return {
            "title": "Nombre incorrecto",
            "type": "formato",
            "message": "El nombre del directorio o archivo no está en el formato correcto.",
        }

    def get_fun_type(self):
        return "name"


class RegexNameValidator(Validator):
    def apply(self):
        path = self.args["path"]
        regex = self.args["name"]
        return True if len(glob.glob(os.path.join(path, regex))) > 0 else False

    def get_error(self):
        return {
            "title": "No existe archivo con expresión regular",
            "type": "formato",
            "message": "No existe directorio o archivo con la expresión regular buscada.",
        }

    def get_fun_type(self):
        return "name"
