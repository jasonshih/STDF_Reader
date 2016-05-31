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


__author__ = 'cahyo primawidodo 2016'


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    # w = Writer()
    # # w.load_stdf_type(json_file='stdf/stdf_v4.json')
    # w.load_stdf_type(json_file='tests/stdf_test.json')

    pass

    stdf = Reader('stdf/stdf_v4.json')
    stdf.load_stdf_file(stdf_file='ASETKH-UFLX0058_1_WSBU-NN450-12B-04p1_1_DP5403.K2_15_20150303175521.stdf')

    size = stdf.STDF_IO.__sizeof__()
    last, now = 0, 0

    with open('output.txt', mode='wt', encoding='utf-8') as fout:
        for rec_name, header, body in stdf:
            now = stdf.STDF_IO.tell()

            if rec_name == 'PRR':
                print(body)

            if (now - last) > 0.1 * size:
                logging.error('*')
                last = now
