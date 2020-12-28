[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
# inputValidator

To check consistency in input files

## Requirements

- Python3
- Dependencies: requirements.txt

## Run tests
To verify that everything works well on your computer you can run these automatic tests that will tell you if there is a problem:

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

    {
        "function": "bounding_box",
        "args": {
            "x_coordinate_index": 2,
            "y_coordinate_index": 3,
        }
    }
* **function**: function name (string)
* **args**: function args (dict(string | list))


#### Children
List of path dicts

    

## Add New Validators

To add new validators you can use existing validators or create new validators
To create a new validator for a configuration file you must modify the `configuration.json` file.

If a configuration dictionary exists for the file, you must add a new validator dict to **formatRules** or **semanticRules**.  
Else you must add the file dict as the [configuration example](#configuration-file).

### Using existing validators

