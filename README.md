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
    >Archivos procesados, los resultados se encuentran en /home/bastianleaf/PycharmProjects/inputValidator/output/errores.csv
