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

import struct
import json
import re


class Writer:

    def __init__(self, stdf_type_json='stdf_v4.json'):
        self.STDF_TYPE = {}
        self.REC_NAME = {}
        self.FMT_MAP = {}
        self.load_fmt_mapping()

        self.e = '<'

        self.load_stdf_type(stdf_type_json)

    def load_stdf_type(self, json_file):
        with open(json_file) as fp:
            self.STDF_TYPE = json.load(fp)

        for k, v in self.STDF_TYPE.items():
            typ_sub = (v['rec_typ'], v['rec_sub'])
            self.REC_NAME[typ_sub] = k

    def load_fmt_mapping(self, json_file=None):

        if json_file is None:
            self.FMT_MAP = {
                "U1": "B",
                "U2": "H",
                "U4": "I",
                "I1": "b",
                "I2": "h",
                "I4": "i",
                "R4": "f",
                "R8": "d",
                "B1": "B",
                "C1": "c",
                "N1": "B"
            }
        else:
            with open(json_file) as fp:
                self.FMT_MAP = json.load(fp)

    @staticmethod
    def __get_multiplier(field, body):
        if field == 'SITE_NUM':
            return body['SITE_CNT']  # SDR (1, 80)

        elif field == 'PMR_INDX':
            return body['INDX_CNT']  # PGR (1, 62)

        elif field in ['GRP_INDX', 'GRP_MODE', 'GRP_RADX', 'PGM_CHAR', 'RTN_CHAR', 'PGM_CHAL', 'RTN_CHAL']:
            return body['GRP_CNT']  # PLR (1, 63)

        elif field in ['RTN_INDX', 'RTN_STAT']:
            return body['RTN_ICNT']  # FTR (15, 20)

        elif field in ['PGM_INDX', 'PGM_STAT']:
            return body['PGM_ICNT']  # FTR (15, 20)

        elif field in ['RTN_STAT', 'RTN_INDX']:
            return body['RTN_ICNT']  # MPR (15, 15)

        elif field in ['RTN_RSLT']:
            return body['RSLT_CNT']  # MPR (15, 15)

        elif field in ['ARR_R8', 'ARR_I2', 'ARR_U4', 'ARR_U2', 'ARR_I1', 'ARR_U1', 'ARR_ICNT', 'ARR_I4', 'ARR_R4']:
            return body[0]

        elif field in ['ARR_N1', 'ARR_Cn', 'ARR_Bn']:
            return body[0]

        else:
            raise ValueError

    def __construct_body(self, fmt_raw, item, body_data, odd_nibble):

        if fmt_raw == 'N1':
            if odd_nibble:
                fmt, dat = self.__translate_nibble(item, odd=True)
                odd_nibble = False
            else:
                fmt, dat = self.__translate_nibble(item, odd=False, lsb=body_data.pop())
                odd_nibble = True
        else:
            fmt, dat = self.__translate(fmt_raw, item)
            odd_nibble = True

        return fmt, dat, odd_nibble

    @staticmethod
    def __translate_nibble(item, odd=True, lsb=0):
        fmt_ret = ''
        dat_ret = []
        if odd:
            fmt_ret = 'B'
            d = item & 0xF
            dat_ret.append(d)

        else:
            d = (item << 4) + lsb
            dat_ret.append(d)

        return fmt_ret, dat_ret

    def __translate(self, fmt_raw, item):
        fmt_ret = ''
        dat_ret = []

        if fmt_raw == 'Cn':
            string, length = item
            fmt_ret += 'B' + str(length) + 's'
            dat_ret.append(length)
            dat_ret.append(string.encode())

        elif fmt_raw == 'Bn':
            length = len(item)
            fmt_ret += 'B' + str(length) + 'B'
            dat_ret.append(length)
            dat_ret.extend(item)

        else:
            fmt_ret += self.FMT_MAP[fmt_raw]
            dat_ret.append(item)

        return fmt_ret, dat_ret

    def _pack_body(self, field_fmt, field_data) -> bytearray:
        body_fmt = ''
        body_data = []
        odd_nibble = True

        for field_name, fmt_raw in field_fmt:
            item = field_data[field_name]

            if fmt_raw.startswith('K'):
                mo = re.match('^K([0xn])(\w{2})', fmt_raw)
                n = self.__get_multiplier(field_name, body_data)
                fmt_act = mo.group(2)

                for i in range(n):

                    fmt, dat, odd_nibble = self.__construct_body(fmt_act, item[i], body_data, odd_nibble)

                    body_fmt += fmt
                    body_data.extend(dat)

            else:
                fmt, dat, odd_nibble = self.__construct_body(fmt_raw, item, body_data, odd_nibble)

                body_fmt += fmt
                body_data.extend(dat)

        return body_fmt, body_data

    @staticmethod
    def _pack_header(length, typ, sub) -> bytearray:
        header_fmt = 'HBB'
        header_data = [length, typ, sub]
        return header_fmt, header_data

    def pack_record(self, rec_name, data):

        mapping = self.STDF_TYPE[rec_name]['body']
        fmt_b, data_b = self._pack_body(mapping, data)

        rec_len = struct.calcsize('HBB' + fmt_b) - 4
        rec_typ = self.STDF_TYPE[rec_name]['rec_typ']
        rec_sub = self.STDF_TYPE[rec_name]['rec_sub']
        fmt_h, data_h = self._pack_header(rec_len, rec_typ, rec_sub)

        fmt = fmt_h + fmt_b
        *d, = data_h + data_b

        return struct.pack(self.e + fmt, *d)

    def pack_FAR(self):

        r = self.pack_record('FAR', {'CPU_TYPE': 2, 'STDF_VER': 4})
        return r
