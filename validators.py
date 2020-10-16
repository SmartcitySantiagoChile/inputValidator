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
    def apply(self) -> bool:
        """
        Return alwasy true
        :return: bool
        """
        return True

    def get_error(self):
        return {
            "title": "Raiz incorrecta",
            "type": "formato",
            "message": "La raíz del directorio debe tener un nombre vacío en la configuración.",
        }

    def get_fun_type(self):
        return "name"


class NameValidator(Validator):
    def apply(self) -> bool:
        """
        Check if file exists in path
        :return: bool
        """
        path = self.args["path"]
        name = self.args["name"]
        real_path = os.path.join(path, name)
        return os.path.exists(real_path)

    def get_error(self):
        return {
            "title": "Nombre incorrecto",
            "type": "formato",
            "message": "El nombre del directorio o archivo {0} no se encuentra en el directorio {1}.".format(
                self.args["name"], self.args["path"]
            ),
        }

    def get_fun_type(self):
        return "name"


class RegexNameValidator(Validator):
    def apply(self) -> bool:
        """
        Check if regex file exist in path
        :return: bool
        """
        path = self.args["path"]
        regex = self.args["name"]
        return True if len(glob.glob(os.path.join(path, regex))) > 0 else False

    def get_error(self):
        return {
            "title": "No existe archivo con expresión regular",
            "type": "formato",
            "message": "No existe directorio o archivo con la expresión regular {0} en el directorio {1} .".format(
                self.args["name"], self.args["path"]
            ),
        }

    def get_fun_type(self):
        return "name"


class MinRowsValidator(Validator):
    counter = 0

    def apply(self) -> bool:
        """
        Apply row counter and check if it has the minimal
        :return: bool
        """
        self.counter += 1
        min_rows = self.args["min"]
        return self.counter >= min_rows

    def get_error(self):
        return {
            "name": "Número de filas menor al correcto",
            "type": "formato",
            "message": "El archivo posee {0} filas, cuando debería tener {1} filas como mínimo".format(
                self.counter, self.args["min"]
            ),
        }

    def get_fun_type(self):
        return "format"


class ASCIIColValidator(Validator):
    row_counter = 0

    def apply(self) -> bool:
        """
        Check if col is in ASCII
        :return: bool
        """
        self.row_counter += 1
        row = self.args["row"]
        col_to_check = self.args["col_index"]
        return row[col_to_check].isascii()

    def get_error(self):
        index = self.args["col_index"]
        var = self.args["row"][index]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "Valor contiene ñ o acentos",
            "type": "formato",
            "message": "La variable {0} posee ñ o acentos en la fila {1}, columna {2}.".format(
                var, self.row_counter, col_name
            ),
        }

    def get_fun_type(self):
        return "format"
