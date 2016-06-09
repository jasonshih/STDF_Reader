"""The MIT License (MIT)
Copyright (c) 2016 Cahyo Primawidodo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE."""

from stdf.stdf_reader import Reader
from stdf.stdf_writer import Writer
import logging
from pathlib import Path

__author__ = 'cahyo primawidodo 2016'


if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR)

    # p = Path('/Users/cahyo/Documents/data/oca')
    p = Path('C:/Users/cahyop/Documents/Python_Scripts/data/oca')
    # in_file = str(p / 'ASETKH-UFLX0079_1_EN1U-NN876-12C-04_July1_1_DP6069.03_06_20150701180653.stdf')
    # in_file = str(p / 'Dev#9_room.std')
    in_file = str(p / 'UFLEX103_PAPAYA-12D_3R38424.1-ENG_1_ES8U-N4958-12D-23p3_Apr09_06_13_36.stdf')

    stdf = Reader()
    stdf.load_stdf_file(stdf_file=in_file)
    stdf.show_known_records()
    # stdf.show_records_structure()

    # with open('output.txt', mode='wt', encoding='utf-8') as fout:
    #     for rec_name, header, body in stdf:
    #
    #         for r in rec_name:
    #             fout.write(r)
    #
    #             if fout.tell() % 100 == 0:
    #                 fout.write('\n')
    #
    #         for k, v in body.items():
    #             fout.write('.')
    #
    #             if fout.tell() % 100 == 0:
    #                 fout.write('\n')
