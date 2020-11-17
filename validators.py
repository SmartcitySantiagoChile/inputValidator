import datetime
import glob
import math
import os
import re
from abc import ABCMeta, abstractmethod

from shapely.geometry import Point, Polygon


def utm_to_wsg84(
    east_coordinate: float,
    north_coordinate: float,
    zone: int = 19,
    north_hemisphere: bool = False,
) -> tuple:
    if not north_hemisphere:
        north_coordinate = 10000000 - north_coordinate

    a = 6378137
    e = 0.081819191
    e1sq = 0.006739497
    k0 = 0.9996

    arc = north_coordinate / k0
    mu = arc / (
        a
        * (
            1
            - math.pow(e, 2) / 4.0
            - 3 * math.pow(e, 4) / 64.0
            - 5 * math.pow(e, 6) / 256.0
        )
    )

    ei = (1 - math.pow((1 - e * e), (1 / 2.0))) / (1 + math.pow((1 - e * e), (1 / 2.0)))

    ca = 3 * ei / 2 - 27 * math.pow(ei, 3) / 32.0

    cb = 21 * math.pow(ei, 2) / 16 - 55 * math.pow(ei, 4) / 32
    cc = 151 * math.pow(ei, 3) / 96
    cd = 1097 * math.pow(ei, 4) / 512
    phi1 = (
        mu
        + ca * math.sin(2 * mu)
        + cb * math.sin(4 * mu)
        + cc * math.sin(6 * mu)
        + cd * math.sin(8 * mu)
    )

    n0 = a / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (1 / 2.0))

    r0 = a * (1 - e * e) / math.pow((1 - math.pow((e * math.sin(phi1)), 2)), (3 / 2.0))
    fact1 = n0 * math.tan(phi1) / r0

    _a1 = 500000 - east_coordinate
    dd0 = _a1 / (n0 * k0)
    fact2 = dd0 * dd0 / 2

    t0 = math.pow(math.tan(phi1), 2)
    q0 = e1sq * math.pow(math.cos(phi1), 2)
    fact3 = (5 + 3 * t0 + 10 * q0 - 4 * q0 * q0 - 9 * e1sq) * math.pow(dd0, 4) / 24

    fact4 = (
        (61 + 90 * t0 + 298 * q0 + 45 * t0 * t0 - 252 * e1sq - 3 * q0 * q0)
        * math.pow(dd0, 6)
        / 720
    )

    lof1 = _a1 / (n0 * k0)
    lof2 = (1 + 2 * t0 + q0) * math.pow(dd0, 3) / 6.0
    lof3 = (
        (5 - 2 * q0 + 28 * t0 - 3 * math.pow(q0, 2) + 8 * e1sq + 24 * math.pow(t0, 2))
        * math.pow(dd0, 5)
        / 120
    )
    _a2 = (lof1 - lof2 + lof3) / math.cos(phi1)
    _a3 = _a2 * 180 / math.pi

    latitude = 180 * (phi1 - fact1 * (fact2 + fact3 + fact4)) / math.pi

    if not north_hemisphere:
        latitude = -latitude

    longitude = ((zone > 0) and (6 * zone - 183.0) or 3.0) - _a3
    return latitude, longitude


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


class TimeValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has time value (HH:MM:SS)
        :return: bool
        """
        time_format = "%H:%M:%S"
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = self.args["row"][col]
            try:
                datetime.datetime.strptime(value, time_format)
            except ValueError:
                self.cols_error.append(col)

        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "Existe un valor en formato de hora incorrecto"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores en formato de hora incorrecto"
            tail = "columnas"

        return {
            "name": "Formato de hora incorrecto",
            "type": "formato",
            "message": "{0} en la fila {1}, {2} {3}.".format(
                head, self.row_counter, tail, ", ".join(cols_names)
            ),
        }

    def get_fun_type(self):
        return "row"


class GreaterThanValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if upper_col is greater than lower_col
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        upper_col = args[self.args["upper_col"]]
        lower_col = args[self.args["lower_col"]]
        comparison_type = self.args["type"]
        if comparison_type == "time":
            time_format = "%H:%M:%S"
            try:
                upper_time = datetime.datetime.strptime(upper_col, time_format)
                lower_time = datetime.datetime.strptime(lower_col, time_format)
            except ValueError:
                return False
            return upper_time > lower_time
        else:
            return upper_col > lower_col

    def get_error(self):
        first_value_header = self.args["header"][self.args["upper_col"]]
        last_value_header = self.args["header"][self.args["lower_col"]]

        return {
            "name": "Inconsistencia entre valores",
            "type": "formato",
            "message": "En la fila {1} el valor de la columna {0} es menor al valor de la columna {2}.".format(
                first_value_header, self.row_counter, last_value_header
            ),
        }

    def get_fun_type(self):
        return "row"


class StoreColValue(Validator):
    def __init__(self, args):
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Save col index in args
        :return: bool
        """
        index = self.args["col_index"]
        var = args[index]
        data_validator = self.args["data_validator"]
        storage_name = self.args["storage_name"]
        if data_validator.storage.get(storage_name, 0) == 0:
            data_validator.storage[storage_name] = [var]
        else:
            data_validator.storage[storage_name].append(var)
        return True

    def get_error(self):

        return {
            "name": "No se puede almacenar valor",
            "type": "formato",
            "message": "Error al almacenar valor",
        }

    def get_fun_type(self):
        return "storage"


class CheckColStorageValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col value is in given storage
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        index = self.args["col_index"]
        val = args[index]
        data_validator = self.args["data_validator"]
        storage = data_validator.storage[self.args["storage_name"]]
        return val in storage

    def get_error(self):
        index = self.args["col_index"]
        var = self.args["row"][index]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "El valor no es válido",
            "type": "valor",
            "message": "La variable {0} no se encuentra en los valares {1} en la fila {2}, columna {3}.".format(
                var, self.args["storage_name"], self.row_counter, col_name
            ),
        }

    def get_fun_type(self):
        return "storage"


class BoundingBoxValueValidator(Validator):
    def __init__(self, args):
        self.row_counter = 0
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if coordinate values are in given bounding box
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        x_coordinate_index = self.args["x_coordinate_index"]
        y_coordinate_index = self.args["y_coordinate_index"]
        x = float(args[x_coordinate_index])
        y = float(args[y_coordinate_index])
        if self.args["coordinate_system"] == "utm":
            x, y = utm_to_wsg84(x, y)
        point = Point(x, y)
        bounding_box = Polygon(self.args["bounding_box"])
        return bounding_box.contains(point)

    def get_error(self):
        x_coordinate_index = self.args["x_coordinate_index"]
        y_coordinate_index = self.args["y_coordinate_index"]
        x = float(self.args["row"][x_coordinate_index])
        y = float(self.args["row"][y_coordinate_index])
        return {
            "name": "Coordenadas inválidas",
            "type": "valor",
            "message": "Las coordenadas {0}, {1} no se encuentran en el rango geográfico correcto.".format(
                x, y
            ),
        }

    def get_fun_type(self):
        return "row"
