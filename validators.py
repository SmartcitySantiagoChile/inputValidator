import glob
import os
from abc import ABCMeta, abstractmethod


class Validator(object, metaclass=ABCMeta):
    def __init__(self, args):
        self.args = args
        super().__init__()

    @abstractmethod
    def apply(self, args=None):
        pass

    @abstractmethod
    def get_error(self):
        pass

    @abstractmethod
    def get_fun_type(self):
        pass


class RootValidator(Validator):
    def apply(self, args=None) -> bool:
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
    def apply(self, args=None) -> bool:
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
    def apply(self, args=None) -> bool:
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
    status = False

    def apply(self, args=None) -> bool:
        """
        Apply row counter and check if it has the minimal
        :return: bool
        """
        self.counter += 1
        min_rows = self.args["min"]
        res = self.counter >= min_rows
        if res:
            self.status = True
        return res

    def get_error(self):
        return {
            "name": "Número de filas menor al correcto",
            "type": "formato",
            "message": "El archivo posee {0} filas, cuando debería tener {1} filas como mínimo".format(
                self.counter, self.args["min"]
            ),
        }

    def get_fun_type(self):
        return "file"


class ASCIIColValidator(Validator):
    row_counter = 0

    def apply(self, args=None) -> bool:
        """
        Check if col is in ASCII
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        col_to_check = self.args["col_index"]
        return self.args["row"][col_to_check].isascii()

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
        return "row"


class DuplicateValueValidator(Validator):
    row_counter = 0
    values = []

    def apply(self, args=None) -> bool:
        """
        Check if col has not duplicated value
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        col_to_check = self.args["col_index"]
        value = self.args["row"][col_to_check]
        print(value)
        print(self.values)
        if value in self.values:
            return False
        else:
            self.values.append(value)
        return True

    def get_error(self):
        index = self.args["col_index"]
        var = self.args["row"][index]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "Valor duplicado",
            "type": "formato",
            "message": "La variable {0} está duplicada en la fila {1}, columna {2}.".format(
                var, self.row_counter, col_name
            ),
        }

    def get_fun_type(self):
        return "row"


class EmptyRowValidator(Validator):
    row_counter = 0

    def apply(self, args=None) -> bool:
        """
        Check if is not empty row
        :return: bool
        """
        self.row_counter += 1
        if args:
            return False
        else:
            return True

    def get_error(self):
        return {
            "name": "Fila vacía",
            "type": "formato",
            "message": "El archivo posee una linea vacía en la fila {0}.".format(
                self.row_counter
            ),
        }

    def get_fun_type(self):
        return "row"


class HeaderValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check header
        :return: bool
        """
        return self.args["header"] == args

    def get_error(self):
        return {
            "name": "Header incorrecto",
            "type": "formato",
            "message": "El header no corresponde al archivo.",
        }

    def get_fun_type(self):
        return "row"
