# STDF Reader 0.1.4
![build](https://img.shields.io/badge/build-passing-brightgreen.svg "passing") ![license](https://img.shields.io/badge/license-MIT%20License-blue.svg) ![tests](https://img.shields.io/badge/tests-passing-green.svg)

Read the binary STDF file (.std), which is the standard test data format
commonly used by Automated Test Equipment such as Teradyne, Advantest and
LTX testers.

### Installation

    pip install stdf

### Usage

    from stdf.stdf_reader import Reader()
    stdf = Reader()
    stdf.load_stdf_file(stdf_file='input_file.std')

    for rec_name, header, body in stdf:
    # iterate stdf file record by record, starting from 'FAR' record.

        if rec_name == 'FAR':
            # body is a dictionary with field name as keys.
            cpu_type = body['CPU_TYPE']

### Documentation

Visit https://pythonhosted.org/stdf/

### Limitation
- STDF V4 format only.
- Python 3.3 and above.
