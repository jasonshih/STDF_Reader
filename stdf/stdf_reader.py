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

import json
import io
import struct
import logging
import re
import math
from os import path

__author__ = 'cahyo primawidodo 2016'


class Reader:
    HEADER_SIZE = 4

    def __init__(self, stdf_ver_json=None):
        self.log = logging.getLogger(self.__class__.__name__)
        self.STDF_TYPE = {}
        self.STDF_IO = io.BytesIO(b'')
        self.REC_NAME = {}
        self.FMT_MAP = {}
        self.e = '<'

        self.body_start = 0

        self._load_byte_fmt_mapping()
        self._load_stdf_type(json_file=stdf_ver_json)

    def _load_stdf_type(self, json_file):

        if json_file is None:
            here = path.abspath(path.dirname(__file__))
            input_file = path.join(here, 'stdf_v4.json')
        else:
            input_file = json_file

        self.log.info('loading STDF configuration file = {}'.format(input_file))
        with open(input_file) as fp:
            self.STDF_TYPE = json.load(fp)

        for k, v in self.STDF_TYPE.items():
            typ_sub = (v['rec_typ'], v['rec_sub'])
            self.REC_NAME[typ_sub] = k

    def _load_byte_fmt_mapping(self):
        self.FMT_MAP = {
            "U1": "B",
            "U2": "H",
            "U4": "I",
            "U8": "Q",
            "I1": "b",
            "I2": "h",
            "I4": "i",
            "I8": "q",
            "R4": "f",
            "R8": "d",
            "B1": "B",
            "C1": "c",
            "N1": "B"
            }

    def load_stdf_file(self, stdf_file):
        self.log.info('opening STDF file = {}'.format(stdf_file))
        with open(stdf_file, mode='rb') as fs:
            self.STDF_IO = io.BytesIO(fs.read())
        self.log.info('detecting STDF file size = {}'.format(len(self.STDF_IO.getvalue())))

    def read_record(self):
        header = self._read_and_unpack_header()

        if header:
            rec_size, _, _ = header
            self.log.debug('BODY start at tell={:0>8}'.format(self.STDF_IO.tell()))
            body_raw = self._read_body(rec_size)
            rec_name, body = self._unpack_body(header, body_raw)
            self.log.debug('BODY end at tell={:0>8}'.format(self.STDF_IO.tell()))

            if rec_name == 'FAR':
                self.__set_endian(body['CPU_TYPE'])

            return rec_name, header, body

        else:
            self.log.info('closing STDF_IO at tell={:0>8}'.format(self.STDF_IO.tell()))
            self.STDF_IO.close()
            return False

    def _read_and_unpack_header(self):
        header_raw = self.STDF_IO.read(self.HEADER_SIZE)

        header = False
        if header_raw:
            header = struct.unpack(self.e + 'HBB', header_raw)
            rec_name = self.REC_NAME.setdefault((header[1], header[2]), 'UNK')
            self.log.debug('len={:0>3}, rec={}'.format(header[0], rec_name))

        return header

    def _read_body(self, rec_size):
        self.body_start = self.STDF_IO.tell()
        body_raw = io.BytesIO(self.STDF_IO.read(rec_size))
        assert len(body_raw.getvalue()) == rec_size
        return body_raw

    def _unpack_body(self, header, body_raw):
        rec_len, rec_typ, rec_sub = header
        typ_sub = (rec_typ, rec_sub)
        rec_name = self.REC_NAME.setdefault(typ_sub, 'UNK')
        max_tell = rec_len
        odd_nibble = True

        body = {}
        if rec_name in self.STDF_TYPE:
            for field, fmt_raw in self.STDF_TYPE[rec_name]['body']:
                self.log.debug('field={}, fmt_raw={}'.format(field, fmt_raw))

                if fmt_raw == 'N1' and not odd_nibble:
                    pass
                elif body_raw.tell() >= max_tell:
                    break

                array_data = []
                if fmt_raw.startswith('K'):
                    mo = re.match('^K([0xn])(\w{2})', fmt_raw)
                    n = self.__get_multiplier(field, body)
                    fmt_act = mo.group(2)

                    for i in range(n):
                        data, odd_nibble = self.__get_data(fmt_act, body_raw, odd_nibble)
                        array_data.append(data)

                    body[field] = array_data
                    odd_nibble = True

                elif fmt_raw.startswith('V'):
                    vn_map = ['B0', 'U1', 'U2', 'U4', 'I1', 'I2',
                              'I4', 'R4', 'R8', 'Cn', 'Bn', 'Dn', 'N1']
                    n, = struct.unpack('H', body_raw.read(2))

                    for i in range(n):
                        idx, = struct.unpack(self.e + 'B', body_raw.read(1))
                        fmt_vn = vn_map[idx]

                        data, odd_nibble = self.__get_data(fmt_vn, body_raw, odd_nibble)
                        array_data.append(data)

                    body[field] = array_data
                    odd_nibble = True

                else:
                    body[field], odd_nibble = self.__get_data(fmt_raw, body_raw, odd_nibble)

        else:
            self.log.warn('record name={} ({}, {}), not found in self.STDF_TYPE'.format(rec_name, rec_typ, rec_sub))

        body_raw.close()
        return rec_name, body

    def __get_data(self, fmt_act, body_raw, odd_nibble):
        data = 0
        if fmt_act == 'N1':
            if odd_nibble:
                nibble, = struct.unpack(self.e + 'B', body_raw.read(1))
                _, data = nibble >> 4, nibble & 0xF
                odd_nibble = False
            else:
                body_raw.seek(-1, 1)
                nibble, = struct.unpack(self.e + 'B', body_raw.read(1))
                data, _ = nibble >> 4, nibble & 0xF
                odd_nibble = True
        else:
            fmt, buf = self.__get_format_and_buffer(fmt_act, body_raw)

            if fmt:
                d = struct.unpack(fmt, buf)
                data = d[0] if len(d) == 1 else d
            odd_nibble = True

        return data, odd_nibble

    def __get_format_and_buffer(self, fmt_raw, body_raw):
        fmt = self.__get_format(fmt_raw, body_raw)
        if fmt:
            size = struct.calcsize(fmt)
            buf = body_raw.read(size)
            self.log.debug('fmt={}, buf={}'.format(fmt, buf))
            return fmt, buf
        else:
            return 0, 0

    def __get_format(self, fmt_raw, body_raw):
        self.log.debug('fmt_raw={}, body_raw={}'.format(fmt_raw, body_raw))

        if fmt_raw in self.FMT_MAP:
            return self.FMT_MAP[fmt_raw]

        elif fmt_raw == 'Sn':
            buf = body_raw.read(2)
            n, = struct.unpack(self.e + 'H', buf)
            posfix = 's'

        elif fmt_raw == 'Cn':
            buf = body_raw.read(1)
            n, = struct.unpack(self.e + 'B', buf)
            posfix = 's'

        elif fmt_raw == 'Bn':
            buf = body_raw.read(1)
            n, = struct.unpack(self.e + 'B', buf)
            posfix = 'B'

        elif fmt_raw == 'Dn':
            buf = body_raw.read(2)
            h, = struct.unpack(self.e + 'H', buf)
            n = math.ceil(h/8)
            posfix = 'B'
        else:
            raise ValueError(fmt_raw, body_raw.tell(), body_raw.__sizeof__())

        return str(n) + posfix if n else ''

    def __set_endian(self, cpu_type):
        if cpu_type == 1:
            self.e = '>'
        elif cpu_type == 2:
            self.e = '<'
        else:
            self.log.critical('Value of FAR: CPU_TYPE is not 1 or 2. Invalid endian.')
            raise IOError(cpu_type)

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

        elif field in ['UPD_NAM']:
            return body['UPD_CNT']  # VUR (0, 30)

        elif field in ["PAT_BGN", "PAT_END", "PAT_FILE", "PAT_FILE", "PAT_LBL", "FILE_UID", "ATPG_DSC", "SRC_ID"]:
            return body["LOCP_CNT"]  # PSR (1, 90)

        elif field in ["PMR_INDX", "ATPG_NAM"]:
            return body["LOCM_CNT"]  # NMR (1, 91)

        elif field in ["CHN_LIST"]:
            return body["CHN_CNT"]  # SSR (1, 93)

        elif field in ["M_CLKS"]:
            return body["MSTR_CNT"]  # CDR (1, 94)

        elif field in ["S_CLKS"]:
            return body["SLAV_CNT"]  # CDR (1, 94)

        elif field in ["CELL_LST"]:
            return body["LST_CNT"]  # CDR (1, 94)

        else:
            raise ValueError

    def __iter__(self):
        return self

    def __next__(self):
        r = self.read_record()
        if r:
            return r
        else:
            raise StopIteration
