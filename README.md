[![Build Status](https://travis-ci.com/SmartcitySantiagoChile/inputValidator.svg?branch=master)](https://travis-ci.com/SmartcitySantiagoChile/fondefVizServer) [![Coverage Status](https://coveralls.io/repos/github/SmartcitySantiagoChile/inputValidator/badge.svg?branch=main)](https://coveralls.io/github/SmartcitySantiagoChile/inputValidator?branch=main) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)  

# inputValidator

To check consistency in input files

## Requirements

- Python3
- Dependencies: requirements.txt

## Run tests

To verify that everything works well on your computer you can run these automatic tests that will tell you if there is a
problem:

    python -m unittest

## Usage

To run inputValidator you need to execute:

    python input_validator.py [-h] [--output OUTPUT]  [-v] path [path ...]

- [path] path file(s)
- [--output]  output name (errores.csv by default)
- [-v] a verbose mode, errors will show in terminal

### Example

    python input_validator.py "input/Original_2020-07JulioUTF8.zip"
    > Archivos procesados, los resultados se encuentran en /home/bastianleaf/PycharmProjects/inputValidator/output/errores.csv

## Configuration File

The configuration file is a JSON file that has all the validation rules for each file.

The configuration structure is like this:

#### Example for path /Rutas/ShapeRutas.csv

```json
{
  "path": {
    "type": "name",
    "name": "Rutas"
  },
  "rules": [],
  "children": [
    {
      "path": {
        "type": "name",
        "name": "ShapeRutas.csv",
        "header": [
          "ID",
          "ROUTE_NAME",
          "X-Coordinate",
          "Y-Coordinate"
        ],
        "dependencies": [
          "Diccionario-Servicios.csv"
        ]
      },
      "rules": {
        "formatRules": [
        ],
        "semanticRules": [
          {
            "function": "check_col_storage_value",
            "args": {
              "col_index": 1,
              "storage_name": "route_name"
            }
          },
          {
            "function": "bounding_box",
            "args": {
              "x_coordinate_index": 2,
              "y_coordinate_index": 3,
              "bounding_box": [
                [
                  -33.316183,
                  -70.889876
                ],
                [
                  -33.316183,
                  -70.461653
                ],
                [
                  -34.190746,
                  -70.461653
                ],
                [
                  -34.190746,
                  -70.889876
                ]
              ],
              "coordinate_system": "utm"
            }
          }
        ]
      },
      "children": []
    }
  ]
}

```

### Configuration file components:

#### Path

Information about filename and header

* **type**: type of path name (string).
    * root: root folder
    * name: folder or file
    * regex: file with regex filename
    * multiregex: multiple files with regex filename

* **name**: name of folder, file or regex (string | list(string))
* **header**(optional): header of file (list(string))
* **dependencies**(optional): dependencies of file (list(string))

#### Rules

Information about validations

* **formatRules**: list of format rules (list(dict))
* **semanticRules**: list of semantic rules (list(dict))

##### Rule

A rule dict has the next structure:

```json
{
  "function": "bounding_box",
  "args": {
    "x_coordinate_index": 2,
    "y_coordinate_index": 3
  }
}
```

* **function**: function name (string)
* **args**: function args (dict(string | list))

#### Children

List of path dicts

## Add New Validators

To add new validators you can use existing validators or create new validators.

The validators are in the `validators.py` file.

A validator is composed by a validator class and validator name. For example `ASCIIColValidator` class has the
name `ascii`.

All validator names are in the `check_name_functions` or `file_functions` dict at the end of the file.

To add a new validator for a configuration file you must modify the `configuration.json` file.

If a configuration dictionary exists for the file, you must add a new validator dict to **formatRules** or **
semanticRules**.  
Else you must add the file dict as the [configuration example](#configuration-file).

### Using existing validators

If you want to use existing validators you must add the validator name and the function arguments to
the `configuration.json`.

Example:

```json5
{
  "function": "string_domain",
  "args": {
    "col_indexes": [
      3
    ],
    "domain": [
      "Ida",
      "Ret"
    ]
  }
}
```

### Creating new validators

To create a new validator you must create a validator class and validator name. The validator class has the next
structure:

```python
class ValidatorClass(Validator):
    def apply(self, args=None) -> bool:
        """
        validate args and return status
        """
        status = True
        return status

    def get_error(self) -> dict:
        """
          return a error dict message with the next structure:
        """
        message = {
            "title": "error title",
            "type": "error type",
            "message": "error message",
            "row": "row number",
            "cols": "column number"
        }
        return message
        
    def get_fun_type(self) -> FunType:
        """
        return the Funtype
        """
        return FunType.NAME
        
```
The validator name must be added to check_name_functions or file_functions:
```python
file_functions = {
  "validator_example": ValidatorClass
}
```

#### Example:

This validators check of a list of columns has empty values.
If found an empty value, it returns False.

```python
class RegexValueValidator(Validator):

  def apply(self, args=None) -> bool:
    """
    Check col value with regex
    :return: bool
    """
    self.row_counter += 1  # count row 
    self.args["row"] = args  # save row to check
    col_to_check = self.args["col_index"] # get col index to check
    value = self.args["row"][col_to_check] # get value of col index
    regex = self.args["regex"] # get regex value to compare
    return True if re.search(regex, value) else False # execute the comparation

  def get_error(self) -> dict:
    index = self.args["col_index"] # get col index
    var = self.args["row"][index] # get col index value
    header = self.args["header"] # get header 
    col_name = header[index] # get header col index name

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
      return FunType.ROW # this validator is a row function

    file_functions = {
      "regex_value": RegexValueValidator
    }

```
A list of validator classes, arguments and names are at the end of this file.









## Validators
### Validators Type
There are 5 types of validators:

|FunType   | Explanation  | 
| ------------- | ------------- |
| NAME| Validators that checks filename|
| ROW| Validators that checks row values|
| FILE| Validators that checks all file values|
| STORAGE| Validators that check and storage row values|
| MULTIROW| Validators that check multiple files|

### Validators List
#### Name Functions

| Validator Class  | Validator Name |Arguments | Explanation |
| ------------- | ------------- | ------------- | --------|
| RootValidator| root| none|  Always true, use it to check the file root.
| NameValidator| name| none|  Check if filename exists. |
| RegexNameValidator| regex| none| Check if regex filename exists.|
| RegexMultiNameValidator| multi-regex| none| Check if multiple regex filename exists.|

#### Row Functions
| Validator Class  | Validator Name |Arguments (type) | Explanation |
| ------------- | ------------- | ------------- | --------|
| ASCIIColValidator| ascii| col_indexes (list)|  Check if value is in ascii for all col_indexes.
| DuplicateValueValidator| duplicate| col_index (string)|  Check if value in col_index is duplicated |
| NotEmptyRowValidator| not_empty_row| none| Check if regex filename exists.|
| StringDomainValueValidator| string_domain-regex| none| Check if multiple regex filename exists.|
| RegexValueValidator| regex_value | col_index(string) regex(string) | Check col value with unix regex pattern. |
| NumericRangeValueValidator | numeric_range | lower_bound (string), upper_bound(string), col_indexes(list(string)). |         Check if col is in numeric range |
| TimeValueValidator | time | col_indexes(list(string)) | Check if col is time value (HH:MM:SS).|
| FloatValueValidator | float | col_indexes(list(string)) | Check if col is float value. |
| GreaterThanValueValidator | greater_than | upper_col(string), lower_col(string), type(string) | Check if upper_col is greater than lower_col.|
| BoundingBoxValueValidator | bounding_box | x_coordinate_index(string), y_coordinate_index(string), coordinate_system(string), bounding_box(list(string)) | Check if coordinate values are in given bounding box. |

#### File Functions
| Validator Class  | Validator Name |Arguments (type) | Explanation |
| ------------- | ------------- | ------------- | --------|
|MinRowsValidator|  min_rows | min (string) |        Apply row counter and check if it has the minimal rows.|
 
#### Storage Functions
| Validator Class  | Validator Name |Arguments (type) | Explanation |
| ------------- | ------------- | ------------- | --------|
|StoreColValue | store_col_value| col_index(string), storage_name(string)|         Save col index in named storage. 
|CheckColStorageValueValidator  | check_col_storage_value| col_index(string), storage_name(string) |         Check if col value is in given storage.|
|StoreColDictValues| store_col_dict_values | storage_name(string), key_index(string),value_indexes(list(string))|         Save cols index in args.
|CheckStoreColDictValuesValidator| check_store_col_dict_values | storage_name(string), key_name(string), value_indexes(list(string)), transform_data(string)|         Check if col value dict is in given storage
|MultiRowColValueValidator| check_store_col_dict_values | storage_name(string), key_name(string), value_indexes(list(string)), transform_data(string)|         Check if col value dict is in given storage.|
|CheckColStorageMultiValueValidator|  check_col_storage_multi_value| storage_name(string), col_index(string), separator(string) |Check if col value is in given storage when col value is a list.|

#### Multirow Functions
| Validator Class  | Validator Name |Arguments (type) | Explanation |
| ------------- | ------------- | ------------- | --------|
|MultiRowColValueValidator| multi_row_col_value| col_indexes(list(string)) |         Check if multiples rows have the same cols value.|



