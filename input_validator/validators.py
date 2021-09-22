import datetime
import glob
import math
import operator
import os
import pathlib
import re
import sys
from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import wraps

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

    Args:

        east_coordinate: easting
        north_coordinate: northing
        zone:  zone
        north_hemisphere: true | false

    Returns:

        tuple: (lat, long)

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
        """
        Init method, it storage args and initialize a row counter

        Args:

            args: validator args

        """
        self.args = args
        self.row_counter = 0
        super().__init__()

    @abstractmethod
    def apply(self, args=None):
        """
        Apply the validator method

        Args:
            args: validator args
        """
        pass

    @abstractmethod
    def get_error(self):
        """
        Method that return a error dict

        The error dict has 4 parameters:

        name: error name
        type: error type
        message: error message
        row: row number
        cols: column number

        """
        pass

    @abstractmethod
    def get_fun_type(self):
        """
        Return the fun type

        The funtype is
        """
        pass


class ColumnValidator(Validator):

    def get_fun_type(self):
        pass

    def get_error(self):
        pass

    def apply(self, args=None):
        pass

    def __init__(self, args):
        self.cols_error = []
        self.not_valid_indexes = []
        super().__init__(args)

    def get_not_valid_cols_indexes(self, row) -> bool:
        """Check if col indexes exist in row, if not return False.


        Returns: True if all indexes are valid in row.

        """
        self.not_valid_indexes = []
        col_indexes = self.args.get("col_indexes", [])
        value_indexes = self.args.get("value_indexes", [])
        if value_indexes:
            col_indexes = value_indexes
        col_index = self.args.get("col_index", None)
        upper_col = self.args.get("upper_col", None)
        lower_col = self.args.get("lower_col", None)
        x_coordinate_index = self.args.get("x_coordinate_index", None)
        y_coordinate_index = self.args.get("y_coordinate_index", None)
        if col_index:
            col_indexes.append(col_index)
        if upper_col:
            col_indexes.append(upper_col)
        if lower_col:
            col_indexes.append(lower_col)
        if x_coordinate_index:
            col_indexes.append(x_coordinate_index)
        if y_coordinate_index:
            col_indexes.append(y_coordinate_index)
        for index in col_indexes:
            if len(row) <= index:
                self.not_valid_indexes.append(index)
        return True if self.not_valid_indexes else False

    @staticmethod
    def check_not_valid_col_indexes(method):
        """Decorator that check if col indexes are valid."""

        @wraps(method)
        def _impl(self, *method_args, **method_kwargs):
            has_invalid_indexes = self.get_not_valid_cols_indexes(*method_args, **method_kwargs)
            if has_invalid_indexes:
                return False
            method_output = method(self, *method_args, **method_kwargs)
            return method_output

        return _impl

    def get_not_valid_col_error(self) -> dict:
        """Check if not valid col error and create formatted message."""
        if not self.not_valid_indexes:
            return {}

        header = self.args["header"]
        cols_names = [header[index] for index in self.not_valid_indexes]
        head = "Columna faltante"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Columnas faltantes"
            tail = "columnas"

        return {
            "name": "Fila inválida",
            "type": "formato",
            "message": f"{head} en la fila {self.row_counter}, {tail} {', '.join(cols_names)}.",
            "row": self.row_counter,
            "cols": cols_names,
        }

    @staticmethod
    def check_not_valid_col_error(method):
        """Decorator that check if col indexes are valid."""

        @wraps(method)
        def _impl(self, *method_args, **method_kwargs):
            has_not_valid_col_error = self.get_not_valid_col_error(*method_args, **method_kwargs)
            if has_not_valid_col_error:
                return has_not_valid_col_error
            method_output = method(self, *method_args, **method_kwargs)
            return method_output

        return _impl


class RootValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Return always true
        """
        return True

    def get_error(self) -> dict:
        """
        Return error dict with info about the validation.

        Returns:
            dict: A dict with all the parameteres

        """
        return {
            "name": "Raiz incorrecta",
            "type": "formato",
            "message": "La raíz del directorio debe tener un nombre vacío en la configuración.",
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.NAME


class NameValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if file exists in path

        Validator args:

            path: name path to search
            name: filename
        """
        path = self.args["path"]
        name = self.args["name"]
        real_path = os.path.join(path, name)
        return os.path.exists(real_path)

    def get_error(self) -> dict:
        return {
            "name": "Nombre incorrecto",
            "type": "formato",
            "message": "El nombre del directorio o archivo '{0}' no se encuentra en el directorio '{1}'.".format(
                self.args["name"], self.args["path"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.NAME


class RegexNameValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if regex file exist in path
        and if date is correct

        Validator args:

            path: path name to search
            name: filename in unix regex format
        """
        path = self.args["path"]
        regex = self.args["name"]
        date = self.args["date"]
        name = glob.glob(os.path.join(path, regex))
        self.args["date_is_in_name"] = True
        if name:
            name = os.path.split(name[0])[1]
            self.args["date_is_in_name"] = date in name
        validator = args
        validator.temp_name = name
        self.args["temp_name"] = name
        return True if len(name) > 0 and self.args["date_is_in_name"] else False

    def get_error(self) -> dict:
        if self.args['date_is_in_name']:
            message = {
                "name": "No existe archivo con expresión regular",
                "type": "formato",
                "message": f"No existe directorio o archivo con la expresión regular '{self.args['name']}' en el directorio '{self.args['path']}' .",
                "row": "",
                "cols": "",
            }
        else:
            message = {
                "name": "Fecha del archivo no corresponde con PO",
                "type": "formato",
                "message": f"La fecha del archivo {self.args['temp_name']} no corresponde a la fecha del programa PO '{self.args['date']}'.",
                "row": "",
                "cols": "",
            }
        return message

    def get_fun_type(self):
        return FunType.NAME


class RegexMultiNameValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if regex file list exist in path

        Validator args:

            path: path name to search
            name: filename list with unix regex format

        """
        path = self.args["path"]
        regex_list = self.args["name"]
        date = self.args["date"]
        name_list = [glob.glob(os.path.join(path, regex)) for regex in regex_list]
        if name_list[0]:
            name_list = [os.path.split(name[0])[1] for name in name_list]
            self.args["names_with_incorrect_date"] = [name for name in name_list if date not in name]
        self.args["name_list"] = name_list
        validator = args
        validator.temp_name = name_list
        return True if len(name_list) == len(regex_list) and not len(self.args["names_with_incorrect_date"]) else False

    def get_error(self) -> dict:
        if not len(self.args["names_with_incorrect_date"]):
            return {
                "name": "No existen archivos con expresiones regulares",
                "type": "formato",
                "message": f"No existen directorios o archivos con la expresión regular '{self.args['name']}' en el directorio '{self.args['path']}' .",
                "row": "",
                "cols": "",
            }
        else:
            if len(self.args["names_with_incorrect_date"]) > 1:
                names = ','.join(self.args["names_with_incorrect_date"])
                message = f"La fecha de los archivos '{names}' no corresponde a la fecha del programa PO '{self.args['date']}' ."
            else:
                message = f"La fecha del archivo '{self.args['names_with_incorrect_date'][0]}' no corresponde a la fecha del programa PO '{self.args['date']}' ."
            return {
                "name": "Fecha de archivos no corresponde con PO",
                "type": "formato",
                "message": message,
                "row": "",
                "cols": "",
            }

    def get_fun_type(self) -> FunType:
        return FunType.NAME


class RegexServiceDetailNameValidator(Validator):
    """This class validate the service detail file's name."""

    def __init__(self, args):
        super().__init__(args)
        self.wrong_date_counter = 0

    def apply(self, args=None) -> bool:
        """Check if regex file list exist in path and check service detail pattern.

        Args:
            path: path name to search
            name: filename list with unix regex format
            date: date to validate
        """

        def string_date_to_date(string_date: str) -> datetime.date:
            return datetime.datetime(int(string_date[:4]), int(string_date[4:6]), int(string_date[6:8]))

        def get_date_from_service_detail(service_detail_date: str) -> (datetime.date, datetime.date):
            lower_date, upper_date = service_detail_date.split('_')[1:3]
            return string_date_to_date(lower_date), string_date_to_date(upper_date)

        path = self.args["path"]
        regex = self.args["name"]
        date = self.args["date"]
        name_list = glob.glob(os.path.join(path, regex))
        valid_name_list = []
        error_date_list = []
        error_format = False
        if name_list:
            name_list = [os.path.split(name)[1] for name in name_list]
            name_list = [[name, *get_date_from_service_detail(name)] for name in name_list]
            # order names by first date
            name_list.sort(key=lambda x: x[1])
            valid_date = string_date_to_date(date)
            last_date = None
            for name, lower_date, upper_date in name_list:
                if last_date:
                    if (lower_date - last_date).days == 1 and lower_date > last_date:
                        valid_name_list.append(name)
                        last_date = upper_date
                    else:
                        error_date_list.append(name)
                else:
                    if lower_date <= valid_date <= upper_date:
                        valid_name_list.append(name)
                        last_date = upper_date
                    else:
                        error_date_list.append(name)

        else:
            error_format = True

        self.args["names_with_incorrect_date"] = error_date_list
        self.args["names_with_incorrect_format"] = error_format
        self.args["name_list"] = valid_name_list

        validator = args
        validator.temp_name = valid_name_list

        return True if len(valid_name_list) else False

    def get_error(self) -> dict:
        if self.args["names_with_incorrect_format"]:
            return {
                "name": "No existen archivos con expresiones regulares",
                "type": "formato",
                "message": f"No existen directorios o archivos con la expresión regular '{self.args['name']}' en el "
                           f"directorio '{self.args['path']}",
                "row": "",
                "cols": "",
            }
        else:
            message = {
                "name": "Fecha de archivo incorrecta",
                "type": "formato",
                "message": f"La fecha del archivo '{self.args['names_with_incorrect_date'][self.wrong_date_counter]}' "
                           f"no corresponde al formato para la fecha del programa PO '{self.args['date']}' ",
                "row": "",
                "cols": "",
            }
            if len(self.args['names_with_incorrect_date']) - 1 > self.wrong_date_counter:
                self.wrong_date_counter += 1
            return message

    def get_fun_type(self) -> FunType:
        return FunType.NAME


class MinRowsValidator(Validator):
    def __init__(self, args):
        self.counter = 0
        self.status = False
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Apply row counter and check if it has the minimal rows

        Validator args:

            min: min rows

        """
        self.counter += 1
        min_rows = self.args["min"]
        res = self.counter >= min_rows
        if res:
            self.status = True
        return res

    def get_error(self) -> dict:
        return {
            "name": "Número de filas menor al correcto",
            "type": "formato",
            "message": "El archivo posee {0} filas, cuando debería tener {1} filas como mínimo.".format(
                self.counter, self.args["min"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.FILE


class ASCIIColValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col is in ASCII

        Validator args:

            col_indexes: column index list to check
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class DuplicateValueValidator(Validator):
    def __init__(self, args):

        self.values = []
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if col has not duplicated value

        Validator args:
            col_index: column index to check

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

    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class NotEmptyRowValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check if is not empty row
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class HeaderValidator(Validator):
    def apply(self, args=None) -> bool:
        """
        Check header

        Validator args:

            header: header to check
        """
        if len(args) == len(self.args["header"]):
            for header, expected_header in zip(args, self.args["header"]):
                if header != expected_header:
                    return False
            return True
        else:
            return False

    def get_error(self) -> dict:
        return {
            "name": "Header incorrecto",
            "type": "formato",
            "message": "El header no corresponde al archivo. Este debe ser: {0}".format(
                self.args["header"]
            ),
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class NotEmptyValueValidator(ColumnValidator):

    def __init__(self, args):
        self.valid_operators = {
            '==': operator.eq,
        }
        super().__init__(args)

    def has_to_ignore(self, conditions):
        result = True
        operator_name = None

        try:
            for condition in conditions:
                first_argument = self.args['row'][int(condition[0])]
                second_argument = condition[2]
                operator_name = condition[1]
                result = result and self.valid_operators[operator_name](first_argument, second_argument)
        except KeyError:
            raise ValueError('Operator "{0}" is not valid'.format(operator_name))

        return result

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col has not empty value

        Validator args:

            col_indexes: column index list
            conditions_to_ignore_row: list of conditions: [[col_index, operator, string], ...]. for instance: "[[1, '==', 'POR DEFINIR']]"
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        cols_to_check = self.args["col_indexes"]

        conditions = self.args["conditions_to_ignore_row"]
        if len(conditions) > 0 and self.has_to_ignore(conditions):
            return True

        for col in cols_to_check:
            value = self.args["row"][col]
            if not value:
                self.cols_error.append(col)
        if len(self.cols_error) == 0:
            return True
        else:
            return False

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class StringDomainValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """ Check if columns are in domain list.

        Validator args:

            domain: string list
            col_indexes: column index list
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class RegexValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check col value with regex

        Validator args:

            col_index: column index to check
            regex: unix regex
        """
        self.row_counter += 1
        self.args["row"] = args
        col_to_check = self.args["col_index"]
        value = self.args["row"][col_to_check]
        regex = self.args["regex"]
        return True if re.search(regex, value) else False

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class NumericRangeValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col is in numeric range

        Validator args:

            lower_bound: min value
            upper_bound: max value
            col_indexes: column index list to check
        """
        self.cols_error = []
        self.row_counter += 1
        self.args["row"] = args
        lower_bound = float(self.args["lower_bound"])
        upper_bound = float(self.args["upper_bound"])
        cols_to_check = self.args["col_indexes"]
        for col in cols_to_check:
            if self.args["row"][col]:
                value = float(self.args["row"][col])
            else:
                value = sys.maxsize
            if value < lower_bound or value > upper_bound:
                self.cols_error.append(col)

        if len(self.cols_error) == 0:
            return True
        else:
            return False

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class TimeValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col is time value (HH:MM:SS)

        Validator args:

            col_indexes: column index list to check
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class FloatValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col is float value

        Validator args:

            col_indexes: column index list
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class GreaterThanValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if upper_col is greater than lower_col

        Validator args:

            upper_col: max value
            lower_col: min value
            type: comparison type (time)
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class StoreColValue(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Save col index in named storage

        Validator args:

            col_index: column index to check
            storage_name: name to save values
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
        return {
            "name": "No se puede almacenar valor",
            "type": "formato",
            "message": "Error al almacenar valor",
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.STORAGE


class CheckColStorageValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col value is in given storage

        Validator args:

            col_index: column index to check
            storage_name: storage name to check data
        """
        self.row_counter += 1
        self.args["row"] = args
        index = self.args["col_index"]
        val = args[index]
        data_validator = self.args["data_validator"]
        storage = data_validator.storage.get(self.args["storage_name"], [])
        return val in storage

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.STORAGE


class BoundingBoxValueValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if coordinate values are in given bounding box

        Validator args:
            x_coordinate_index: column index of x coordinate
            y_coordinate_index: column index of y coordinate
            coordinate_system: coordinate system (utm, wgs84)
            bounding_box: coordinates list that represent a bounding box
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class StoreColDictValues(ColumnValidator):
    def apply(self, args=None) -> bool:
        """
        Save cols index in args

        Validator args:

            storage_name: storage name to save data
            key_index: key index to save data
            value_indexes: column index list to check

        """
        key_index = self.args["key_index"]
        value_indexes = self.args["value_indexes"]
        key_value = args[key_index]
        data_validator = self.args["data_validator"]
        storage_name = self.args["storage_name"]
        unique = True if self.args.get("unique") == "True" else False
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
        if unique:
            var = var[0]
        value_dict[key_value].append(var)
        data_validator.storage[storage_name] = value_dict
        return True

    def get_error(self) -> dict:
        return {
            "name": "No se puede almacenar valor",
            "type": "formato",
            "message": "Error al almacenar valor",
            "row": "",
            "cols": "",
        }

    def get_fun_type(self) -> FunType:
        return FunType.STORAGE


class CheckStoreColDictValuesValidator(ColumnValidator):

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col value dict is in given storage

        Validator args:

            storage_name: storage name to check
            key_name: key name to check in storage
            value_indexes: column index list to check
            transform_data: transform data value if needed (wsg84_to_utm)
        """
        self.row_counter += 1
        self.args["row"] = args
        key_name = self.args["key_name"]
        value_indexes = self.args["value_indexes"]
        values = [float(args[value]) for value in value_indexes]
        data_validator = self.args["data_validator"]
        storage = data_validator.storage.get(self.args["storage_name"], [])
        storage_key = storage.get(key_name, []) if storage != [] else []
        transform_data = self.args.get("transform_data", [])
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
        elif transform_data == "None":
            res = True if args[value_indexes[0]] in storage_key else False
        else:
            for storage_values in storage_key:
                storage_values = [float(storage_values[0]), float(storage_values[1])]
                if math.isclose(
                        storage_values[0], values[0], abs_tol=0.1
                ) and math.isclose(storage_values[1], values[1], abs_tol=0.1):
                    res = True
                    break
        return res

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.STORAGE


class CheckColStorageMultiValueValidator(ColumnValidator):
    def __init__(self, args):
        super().__init__(args)

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """
        Check if col value is in given storage when col value is a list

        Validator args:

            col_index: col index to check
            storage_name: storage name to check data
            separator: separator of stored data
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

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
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

    def get_fun_type(self) -> FunType:
        return FunType.STORAGE


class MultiRowColValueValidator(Validator):
    def __init__(self, args):
        self.row_number_error = [0]
        super().__init__(args)

    def apply(self, args=None) -> bool:
        """
        Check if multiples rows have the same cols value

        Validator args:

            col_indexes: column index list to check
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

    def get_error(self) -> dict:
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
            "type": "valor",
            "message": "{0} {4} en la fila {1}, {2} {3}.".format(
                head, self.row_counter, tail, ", ".join(cols_names), error_file_names
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self) -> FunType:
        return FunType.MULTIROW


class CompareValueValidator(ColumnValidator):

    def __init__(self, args):
        super().__init__(args)
        self.comparators_translator = {
            "year_in_date": "año en fecha",
            "month_in_date": "mes en fecha",
            "day_name_in_date": "nombre del día en fecha"
        }

    @staticmethod
    def check_year_in_date(year, date):
        year_datetime = datetime.date(int(year), 1, 1)
        date_datetime = datetime.datetime.strptime(date, "%Y-%m-%d")
        return year_datetime.year == date_datetime.year

    @staticmethod
    def check_month_in_date(month, date):
        month_datetime = datetime.date(1, int(month), 1)
        date_datetime = datetime.datetime.strptime(date, "%Y-%m-%d")
        return month_datetime.month == date_datetime.month

    @staticmethod
    def check_day_name_in_date(day_name, date):
        week_day_dict = {
            "LUNES": 0,
            "MARTES": 1,
            "MIERCOLES": 2,
            "JUEVES": 3,
            "VIERNES": 4,
            "SABADO": 5,
            "DOMINGO": 6
        }
        date_datetime = datetime.datetime.strptime(date, "%Y-%m-%d")
        return week_day_dict[day_name] == date_datetime.weekday()

    comparators = {
        "year_in_date": check_year_in_date.__func__,
        "month_in_date": check_month_in_date.__func__,
        "day_name_in_date": check_day_name_in_date.__func__
    }

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """Check comparator method for two col values.

        The comparator methods are defined like static class methods and named in comparator dict.

        Validator args:
            col_indexes: column index list to check
        """
        self.row_counter += 1
        row = args
        comparator = self.args["comparator"]
        col_indexes = self.args["col_indexes"]
        return self.comparators[comparator](row[col_indexes[0]], row[col_indexes[1]])

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
        header = self.args["header"]
        cols_names = [header[index] for index in self.args["col_indexes"]]
        head = "Valor incorrecto"
        tail = "columna"
        if len(cols_names) > 1:
            head = "Existen valores incorrectos"
            tail = "columnas"

        return {
            "name": "Valor incorrecto",
            "type": "valor",
            "message": "{0} en la fila {1}, {2} {3}, comparación incorrecta: '{4}'.".format(
                head, self.row_counter, tail, ", ".join(cols_names),
                self.comparators_translator[self.args["comparator"]]
            ),
            "row": self.row_counter,
            "cols": cols_names,
        }

    def get_fun_type(self) -> FunType:
        return FunType.ROW


class DateConsistencyValidator(ColumnValidator):

    def __init__(self, args):
        self.current_date = None
        super().__init__(args)

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """ Check if the current date col is the next day of the past col date

        Validator args:
            col_index: col index of the date to check
        """

        self.row_counter += 1
        row = args
        row_date = datetime.datetime.strptime(row[self.args["col_index"]], "%Y-%m-%d")
        one_day = datetime.timedelta(days=1)
        if not self.current_date or row_date == self.current_date:
            self.current_date = row_date + one_day
            return True
        return False

    def get_fun_type(self) -> FunType:
        return FunType.ROW

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
        header = self.args["header"]
        col_name = header[self.args["col_index"]]
        return {
            "name": "Fecha inconsistente",
            "type": "valor",
            "message": f"Fecha incosistente en la fila {self.row_counter}, columna {col_name}"
                       f", fecha inconsistente respecto a la fecha anterior.",
            "row": self.row_counter,
            "cols": col_name,
        }


class CompleteYearFileConsistencyValidator(ColumnValidator):
    def __init__(self, args):
        date_str = pathlib.Path(args["file_name"]).stem.split("_")[-1]
        self.op_date = datetime.datetime.strptime(date_str, "%Y%m%d")
        self.current_date = self.op_date
        self.last_date = datetime.datetime(self.op_date.year, 12, 31)
        self.status = False
        self.row_counter = 0
        self.date_found = False
        super().__init__(args)

    @ColumnValidator.check_not_valid_col_indexes
    def apply(self, args=None) -> bool:
        """ Check if the file has a complete year based on op date.

        Validator args:
            col_index:  index to check date
        """
        status = False
        row = args
        date_to_check = datetime.datetime.strptime(row[2], "%Y-%m-%d")
        one_day = datetime.timedelta(days=1)

        # if PO date found start to check
        if date_to_check == self.op_date:
            self.date_found = True
        if self.date_found:
            if date_to_check == self.current_date:
                if date_to_check == self.last_date:
                    status = True
                    self.status = status
                # Increment row counter when date found and current day valid
                self.row_counter += 1
                self.current_date += one_day
        else:
            # Increment row counter when not date found
            self.row_counter += 1

        return status

    def get_fun_type(self) -> FunType:
        return FunType.FILE

    @ColumnValidator.check_not_valid_col_error
    def get_error(self) -> dict:
        header = self.args["header"]
        col_name = header[self.args["col_index"]]
        return {
            "name": "Fechas faltantes",
            "type": "formato",
            "message": f"Fechas faltantes a partir de la fila {self.row_counter}, columna {col_name}.",
            "row": self.row_counter,
            "cols": col_name,
        }


check_name_functions = {

    "name": NameValidator,
    "regex": RegexNameValidator,
    "root": RootValidator,
    "multi-regex": RegexMultiNameValidator,
    "service_detail_regex": RegexServiceDetailNameValidator

}

file_functions = {
    "min_rows": MinRowsValidator,
    "ascii": ASCIIColValidator,
    "duplicate": DuplicateValueValidator,
    "not_empty_row": NotEmptyRowValidator,
    "string_domain": StringDomainValueValidator,
    "regex_value": RegexValueValidator,
    "numeric_range": NumericRangeValueValidator,
    "greater_than": GreaterThanValueValidator,
    "float": FloatValueValidator,
    "time": TimeValueValidator,
    "not_empty_col": NotEmptyValueValidator,
    "store_col_value": StoreColValue,
    "check_col_storage_value": CheckColStorageValueValidator,
    "bounding_box": BoundingBoxValueValidator,
    "store_col_dict_values": StoreColDictValues,
    "check_store_col_dict_values": CheckStoreColDictValuesValidator,
    "check_col_storage_multi_value": CheckColStorageMultiValueValidator,
    "multi_row_col_value": MultiRowColValueValidator,
    "compare_value": CompareValueValidator,
    "date_consistency": DateConsistencyValidator,
    "complete_year_file_consistency": CompleteYearFileConsistencyValidator
}
