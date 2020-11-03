import glob
import os
import re
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
    def __init__(self, args):
        self.row_counter = 0
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col is in ASCII
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = self.args["row"][col]
            if not value.isascii():
                self.cols_error.append(col)

        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        var = [self.args["row"][index] for index in self.cols_error]
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "La variable"
        mid = "posee ñ o acentos en la fila"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Las variables"
            mid = "poseen ñ o acentos en la fila"
            tail = "columnas"

        return {
            "name": "Valores contienen ñ o acentos",
            "type": "formato",
            "message": "{0} {1} {2} {3} {4} {5}.".format(
                head, var, mid, self.row_counter, tail, ", ".join(cols_names)
            ),
        }

    def get_fun_type(self):
        return "row"


class DuplicateValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        self.values = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has not duplicated value
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        col_to_check = self.args["col_index"]
        value = self.args["row"][col_to_check]
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


class NotEmptyRowValidator(Validator):
    row_counter = 0

    def apply(self, args=None) -> bool:
        """
        Check if is not empty row
        :return: bool
        """
        self.row_counter += 1
        if not args:
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


class NotEmptyValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has not empty value
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = self.args["row"][col]
            if not value:
                self.cols_error.append(col)
        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "Existe un valor vacío"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores vacíos"
            tail = "columnas"

        return {
            "name": "Valor vacío",
            "type": "formato",
            "message": "{0} en la fila {1}, {2} {3}.".format(
                head, self.row_counter, tail, ", ".join(cols_names)
            ),
        }

    def get_fun_type(self):
        return "row"


class StringDomainValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has domain values
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        domain = self.args["domain"]
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = self.args["row"][col]
            if value not in domain:
                self.cols_error.append(col)

        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "Existe un valor incorrecto"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores incorrectos"
            tail = "columnas"

        return {
            "name": "Valores incorrectos",
            "type": "formato",
            "message": "{0} en la fila {1}, {2} {3}. Los valores solo pueden ser {4}".format(
                head, self.row_counter, tail, ", ".join(cols_names), self.args["domain"]
            ),
        }

    def get_fun_type(self):
        return "row"


class RegexValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check col value with regex
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        col_to_check = self.args["col_index"]
        value = self.args["row"][col_to_check]
        regex = self.args["regex"]
        return True if re.search(regex, value) else False

    def get_error(self):
        index = self.args["col_index"]
        var = self.args["row"][index]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "El valor no cumple con la expresión regular",
            "type": "formato",
            "message": "La variable {0} no cumple con el formato {1} en la fila {2}, columna {3}.".format(
                var, self.args["regex_name"], self.row_counter, col_name
            ),
        }

    def get_fun_type(self):
        return "row"


class NumericRangeValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col is in numeric range
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        lower_bound = int(self.args["lower_bound"])
        upper_bound = int(self.args["upper_bound"])
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = int(self.args["row"][col])
            if value < lower_bound or value > upper_bound:
                self.cols_error.append(col)

        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "Valor fuera de rango"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Valores fuera de rango"
            tail = "columnas"

        return {
            "name": "Valores fuera de rango",
            "type": "formato",
            "message": "{0} {1} en la fila {2}, {3} {4}. Los valores solo pueden ser parte del rango {5}".format(
                head,
                self.cols_error,
                self.row_counter,
                tail,
                ", ".join(cols_names),
                [self.args["lower_bound"], self.args["upper_bound"]],
            ),
        }

    def get_fun_type(self):
        return "row"
