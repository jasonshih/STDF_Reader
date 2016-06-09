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
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict

__author__ = 'cahyo primawidodo 2016'


if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR)

    # p = Path('/Users/cahyo/Documents/data/oca')
    p = Path('C:/Users/cahyop/Documents/Python_Scripts/data/oca')
    in_file = str(p / 'ASETKH-UFLX0079_1_EN1U-NN876-12C-04_July1_1_DP6069.03_06_20150701180653.stdf')
    # in_file = str(p / 'Dev#9_room.std')
    # in_file = str(p / 'UFLEX103_PAPAYA-12D_3R38424.1-ENG_1_ES8U-N4958-12D-23p3_Apr09_06_13_36.stdf')

    stdf = Reader()
    stdf.load_stdf_file(stdf_file=in_file)
    # stdf.show_known_records()
    # stdf.show_records_structure()

    header_data = {}
    part_data = {}
    run_data = defaultdict(dict)
    test_data = {}

    count = Counter()
    rec_last = None
    valid_site = []
    is_part_record = False

    for rec_name, header, body in stdf:
        if rec_name in stdf.HEADER_RECORDS:
            header_data.update(body)

        if rec_name == 'PIR':
            # beginning of touch down. expect next: PTR, MPR, FTR, STR, BPS, EPS, DTR
            if rec_last == rec_name:
                count['enabled_site'] += 1
            else:
                count['insertion'] += 1
                count['enabled_site'] = 1
            valid_site.append(body['SITE_NUM'])

        elif valid_site and 'SITE_NUM' in body and 'TEST_TXT' in body:
            # PTR or FTR
            test_name = body['TEST_TXT'].split('<>')[-1].strip()
            site_num = body['SITE_NUM']
            result = body['RESULT']
            run_data[site_num].update({test_name: result})
            test_data[test_name] = body
            try:
                del test_data[test_name]['RESULT']
            except:
                pass
            # print('S{:02d} {:30s} {:5.3f}'.format(body['SITE_NUM'], test_name, body['RESULT']))

        elif rec_name == 'PRR':
            site_num = body['SITE_NUM']
            part_id = int(body['PART_ID'])
            part_data[part_id] = body
            part_data[part_id].update(run_data[site_num])
            valid_site.clear()
            run_data[site_num].clear()
            # end of touch down
        else:
            if rec_last != rec_name:
                print('unhandled: {}'.format(rec_name))

        rec_last = rec_name
