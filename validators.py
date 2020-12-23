import datetime
import glob
import math
import os
import re
from abc import ABCMeta, abstractmethod
from enum import Enum

from shapely.geometry import Point, Polygon


class FunType(Enum):
    NAME = 1
    ROW = 2
    FILE = 3
    STORAGE = 4
    MULTIROW = 5


def utm_to_wsg84(
    east_coordinate: float,
    north_coordinate: float,
    zone: int = 19,
    north_hemisphere: bool = False,
) -> tuple:
    """
    Convert utm to wsg84 coordinates
    :param east_coordinate: easting
    :param north_coordinate: northing
    :param zone: zone
    :param north_hemisphere: true | false
    :return: (lat, long)
    """
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
        self.row_counter = 0
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
        Return always true
        :return: bool
        """
        return True

    def get_error(self):
        return {
            "title": "Raiz incorrecta",
            "type": "formato",
            "message": "La raíz del directorio debe tener un nombre vacío en la configuración.",
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.NAME


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
            "message": "El nombre del directorio o archivo '{0}' no se encuentra en el directorio '{1}'.".format(
                self.args["name"], self.args["path"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.NAME


class RegexNameValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if regex file exist in path
        :return: bool
        """
        path = self.args["path"]
        regex = self.args["name"]
        name = glob.glob(os.path.join(path, regex))
        if name:
            name = os.path.split(name[0])[1]
        validator = args
        validator.temp_name = name
        return True if len(name) > 0 else False

    def get_error(self):
        return {
            "title": "No existe archivo con expresión regular",
            "type": "formato",
            "message": "No existe directorio o archivo con la expresión regular '{0}' en el directorio '{1}' .".format(
                self.args["name"], self.args["path"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.NAME


class RegexMultiNameValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if regex file list exist in path
        :return: bool
        """
        path = self.args["path"]
        regex_list = self.args["name"]
        name_list = [glob.glob(os.path.join(path, regex)) for regex in regex_list]

        if name_list[0]:
            name_list = [os.path.split(name[0])[1] for name in name_list]
        validator = args
        validator.temp_name = name_list
        return True if len(name_list) > 0 else False

    def get_error(self):
        return {
            "title": "No existen archivos con expresiones regulares",
            "type": "formato",
            "message": "No existen directorios o archivos con la expresión regular '{0}' en el directorio '{1}' .".format(
                self.args["name"], self.args["path"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.NAME


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
            "message": "El archivo posee {0} filas, cuando debería tener {1} filas como mínimo.".format(
                self.counter, self.args["min"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.FILE


class ASCIIColValidator(Validator):
    def __init__(self, args):

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
            "message": "{0} '{1}' {2} {3} {4} {5}.".format(
                head, var, mid, self.row_counter, tail, ", ".join(cols_names)
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class DuplicateValueValidator(Validator):
    def __init__(self, args):

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
            "message": "La variable '{0}' está duplicada en la fila {1}, columna {2}.".format(
                var, self.row_counter, col_name
            ),
            "row": self.row_counter,
            "cols": col_name,
        }

    def get_fun_type(self):
        return FunType.ROW


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
            "row": self.row_counter,
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.ROW


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
            "message": "El header no corresponde al archivo. Este debe ser: {0}".format(
                self.args["header"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.ROW


class NotEmptyValueValidator(Validator):
    def __init__(self, args):

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
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class StringDomainValueValidator(Validator):
    def __init__(self, args):

        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has domain values
        args:{
            domain -> list
            col_indexes -> list
        }
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
            "message": "{0} en la fila {1}, {2} {3}. Los valores solo pueden ser '{4}'".format(
                head, self.row_counter, tail, ", ".join(cols_names), self.args["domain"]
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class RegexValueValidator(Validator):
    def __init__(self, args):
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
            "message": "La variable '{0}' no cumple con el formato {1} en la fila {2}, columna {3}.".format(
                var, self.args["regex_name"], self.row_counter, col_name
            ),
            "row": self.row_counter,
            "cols": col_name,
        }

    def get_fun_type(self):
        return FunType.ROW


class NumericRangeValueValidator(Validator):
    def __init__(self, args):

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
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class TimeValueValidator(Validator):
    def __init__(self, args):
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
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class FloatValueValidator(Validator):
    def __init__(self, args):
        self.cols_error = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has float value
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            value = self.args["row"][col]
            if not value.replace(".", "", 1).isdigit():
                self.cols_error.append(col)
        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.cols_error]
        head = "Existe un valor en formato distinto a float"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores en formato distinto a float"
            tail = "columnas"

        return {
            "name": "Formato float incorrecto",
            "type": "formato",
            "message": "{0} en la fila {1}, {2} {3}.".format(
                head, self.row_counter, tail, ", ".join(cols_names)
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.ROW


class GreaterThanValueValidator(Validator):
    def __init__(self, args):

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
            "row": self.row_counter,
            "cols": [first_value_header, last_value_header],
        }

    def get_fun_type(self):
        return FunType.ROW


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
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.STORAGE


class CheckColStorageValueValidator(Validator):
    def __init__(self, args):
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col value is in given storage
        args:{
            col_index -> int
            storage_name -> string
        }
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        index = self.args["col_index"]
        val = args[index]
        data_validator = self.args["data_validator"]
        storage = data_validator.storage.get(self.args["storage_name"], [])
        return val in storage

    def get_error(self):
        index = self.args["col_index"]
        var = self.args["row"][index]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "El valor no es válido",
            "type": "valor",
            "message": "La variable '{0}' no se encuentra en los valores válidos para '{1}' en la fila {2}, columna {3}.".format(
                var, self.args["storage_name"], self.row_counter, col_name
            ),
            "row": self.row_counter,
            "cols": col_name,
        }

    def get_fun_type(self):
        return FunType.STORAGE


class BoundingBoxValueValidator(Validator):
    def __init__(self, args):
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
            x, y = utm_to_wsg84(x, y, 19)
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
            "message": "Las coordenadas '{0}', '{1}' en la fila {2} no se encuentran en el rango geográfico correcto.".format(
                x, y, self.row_counter
            ),
            "row": self.row_counter,
            "cols": [
                self.args["header"][x_coordinate_index],
                self.args["header"][y_coordinate_index],
            ],
        }

    def get_fun_type(self):
        return FunType.ROW


class StoreColDictValues(Validator):
    def apply(self, args=None) -> bool:
        """
        Save cols index in args
        :return: bool
        """
        key_index = self.args["key_index"]
        value_indexes = self.args["value_indexes"]
        key_value = args[key_index]
        data_validator = self.args["data_validator"]
        storage_name = self.args["storage_name"]
        if data_validator.storage.get(storage_name, 0) == 0:
            value_dict = {key_value: []}
        else:
            if data_validator.storage[storage_name].get(key_value, 0) == 0:
                value_dict = data_validator.storage[storage_name]
                value_dict[key_value] = []
            else:
                value_dict = data_validator.storage[storage_name]
        var = []
        for value in value_indexes:
            var.append(args[value])
        value_dict[key_value].append(var)
        data_validator.storage[storage_name] = value_dict
        return True

    def get_error(self):

        return {
            "name": "No se puede almacenar valor",
            "type": "formato",
            "message": "Error al almacenar valor",
            "row": "",
            "cols": "",
        }

    def get_fun_type(self):
        return FunType.STORAGE


class CheckStoreColDictValuesValidator(Validator):
    def __init__(self, args):
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col value dict is in given storage
        :param args: {
            key_name -> string
            value_indexes -> list
            storage_name -> string
            transform_data -> string
        }
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        key_name = self.args["key_name"]
        value_indexes = self.args["value_indexes"]
        values = [float(args[value]) for value in value_indexes]
        data_validator = self.args["data_validator"]
        storage = data_validator.storage.get(self.args["storage_name"], [])
        storage_key = storage.get(key_name, []) if storage != [] else []
        transform_data = self.args["transform_data"]
        res = False
        if transform_data == "wsg84_to_utm":
            for storage_values in storage_key:
                storage_values = utm_to_wsg84(
                    float(storage_values[0]), float(storage_values[1])
                )
                if math.isclose(
                    storage_values[0], values[0], abs_tol=0.1
                ) and math.isclose(storage_values[1], values[1], abs_tol=0.1):
                    res = True
                    break
        elif transform_data == "wsg84_to_utm_as_bounding_box":
            point = Point(*values)
            bounding_box = []
            for storage_values in storage_key:
                storage_values = utm_to_wsg84(
                    float(storage_values[0]), float(storage_values[1])
                )
                bounding_box.append(storage_values)
            bounding_box = Polygon(bounding_box)
            res = bounding_box.contains(point)
        else:
            for storage_values in storage_key:
                storage_values = [float(storage_values[0]), float(storage_values[1])]
                if math.isclose(
                    storage_values[0], values[0], abs_tol=0.1
                ) and math.isclose(storage_values[1], values[1], abs_tol=0.1):
                    res = True
                    break
        return res

    def get_error(self):
        header = self.args["header"]
        cols_names = [header[index] for index in self.args["value_indexes"]]
        var = [self.args["row"][value] for value in self.args["value_indexes"]]
        head = "no se encuentra"
        tail = "columna"
        if len(cols_names) > 1:
            head = "no se encuentran"
            tail = "columnas"

        return {
            "name": "El valor no es válido",
            "type": "valor",
            "message": "'{0}' {1} en los valores válidos para {2} en la fila {3}, {4} {5}.".format(
                var, head, self.args["key_name"], self.row_counter, tail, cols_names
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.STORAGE


class CheckColStorageMultiValueValidator(Validator):
    def __init__(self, args):
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col value is in given storage when col value is a list
        args:{
            col_index -> int
            storage_name -> string
        }
        :return: bool
        """
        self.row_counter += 1
        self.args["row"] = args
        index = self.args["col_index"]
        separator = self.args["separator"]
        values = args[index].split(separator)
        data_validator = self.args["data_validator"]
        storage = data_validator.storage.get(self.args["storage_name"], [])
        status = True
        self.args["error_values"] = []
        for val in values:
            if val not in storage:
                self.args["error_values"].append(val)
                status = False

        return status

    def get_error(self):
        index = self.args["col_index"]
        header = self.args["header"]
        col_name = header[index]

        return {
            "name": "El valor no es válido",
            "type": "valor",
            "message": "La variable '{0}' no se encuentra en los valores válidos para {1} en la fila {2}, columna {3}.".format(
                self.args["error_values"],
                self.args["storage_name"],
                self.row_counter,
                col_name,
            ),
            "row": self.row_counter,
            "cols": col_name,
        }

    def get_fun_type(self):
        return FunType.STORAGE


class MultiRowColValueValidator(Validator):
    def __init__(self, args):
        self.cols_error = []
        self.row_number_error = [0]
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if multiples rows have the same cols value
        :return: bool
        """
        self.cols_error = []
        self.row_counter += 1
        # multiple rows
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]
        base_row = self.args["row"][0]
        row_number = 0
        for row in self.args["row"]:
            for col in cols_to_check:
                if not row[col] == base_row[col]:
                    self.cols_error.append(col)
                    self.row_number_error.append(row_number)
            row_number += 1
        if len(self.cols_error) == 0:
            return True
        else:
            return False

    def get_error(self):
        header = self.args["header"]
        file_names = self.args["file_names"]
        error_file_names = [file_names[index] for index in self.row_number_error]
        cols_names = [header[index] for index in self.cols_error]
        head = "Existe un valor en distinto en los archivos"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores distintos en los archivos"
            tail = "columnas"

        return {
            "name": "Valores distintos en archivos",
            "type": "formato",
            "message": "{0} {4} en la fila {1}, {2} {3}.".format(
                head, self.row_counter, tail, ", ".join(cols_names), error_file_names
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self):
        return FunType.MULTIROW
