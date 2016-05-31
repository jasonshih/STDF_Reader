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

__author__ = 'cahyo primawidodo 2016'


class Reader:
    HEADER_SIZE = 4
    # NOT YET Verified: Bn, Vn

    def __init__(self, stdf_type_json='stdf_v4.json'):
        self.log = logging.getLogger(self.__class__.__name__)
        self.STDF_TYPE = {}
        self.STDF_IO = io.BytesIO(b'')
        self.REC_NAME = {}
        self.FMT_MAP = {}
        self.e = '<'

        self.body_start = 0

        self.load_fmt_mapping()
        self.load_stdf_type(json_file=stdf_type_json)

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

    def load_stdf_file(self, stdf_file):
        folder = '/Users/cahyo/Documents/data/oca/'
        with open(folder + stdf_file, mode='rb') as fs:
            self.STDF_IO = io.BytesIO(fs.read())

    def read_record(self):
        header = self._read_and_unpack_header()
        # rec_name = self.REC_NAME.setdefault((header[1], header[2]), 'UNK')
        # self.log.debug('len={:0>3}, rec={}'.format(header[0], rec_name))

        if header:
            rec_size, _, _ = header
            self.log.debug('BODY start at tell={:0>8}'.format(self.STDF_IO.tell()))
            self.body_start = self.STDF_IO.tell()
            body_raw = self._read_body(rec_size)
            rec_name, body = self._unpack_body(header, body_raw)
            self.log.debug('BODY end at tell={:0>8}'.format(self.STDF_IO.tell()))
            return rec_name, header, body
        else:
            self.log.error('closing STDF_IO at tell={:0>8}'.format(self.STDF_IO.tell()))
            self.STDF_IO.close()
            return False

    def _read_and_unpack_header(self):
        header_raw = self.STDF_IO.read(self.HEADER_SIZE)
        if header_raw:
            return struct.unpack(self.e + 'HBB', header_raw)
        else:
            return False

    def _read_body(self, rec_size):
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

                    for i in range(n):
                        fmt_act = mo.group(2)
                        fmt, buf = self.__get_data(fmt_act, body_raw)
                        d, = struct.unpack(self.e + fmt, buf)
                        array_data.append(d)
                    body[field] = array_data
                    odd_nibble = True

                elif fmt_raw.startswith('V'):
                    vn_map = ['B0', 'U1', 'U2', 'U4', 'I1', 'I2',
                              'I4', 'R4', 'R8', 'Cn', 'Bn', 'Dn', 'N1']
                    n, = struct.unpack('H', body_raw.read(2))

                    for i in range(n):
                        idx = 0
                        while idx == 0:
                            idx, = struct.unpack(self.e + 'B', body_raw.read(1))
                        fmt_vn = vn_map[idx]
                        fmt, buf = self.__get_data(fmt_vn, body_raw)
                        d, = struct.unpack(self.e + fmt, buf)
                        array_data.append(d)
                    body[field] = array_data
                    odd_nibble = True

                elif fmt_raw == 'N1':
                    if odd_nibble:
                        fmt, buf = self.__get_data(fmt_raw, body_raw)
                        nibble, = struct.unpack(self.e + fmt, buf)
                        lsb = nibble & 0xF
                        msb = nibble >> 4
                        body[field] = lsb
                        odd_nibble = False
                    else:
                        body[field] = msb
                        odd_nibble = True

                else:
                    fmt, buf = self.__get_data(fmt_raw, body_raw)

                    if fmt_raw == 'Bn':
                        body[field] = struct.unpack(fmt, buf)
                    else:
                        body[field], = struct.unpack(fmt, buf)

                    odd_nibble = True
        else:
            self.log.error('record name={} ({}, {}), not found in self.STDF_TYPE'.format(rec_name, rec_typ, rec_sub))

        # if rec_name not in ['EPS']:
        #     self.log.debug('header={}, body={}'.format(rec_name, str(body)[:50]))

        body_raw.close()
        return rec_name, body

    def __get_data(self, fmt_raw, body_raw):
        fmt = self.__get_format(fmt_raw, body_raw)
        size = struct.calcsize(fmt)

        buf = body_raw.read(size)
        self.log.debug('fmt={}, buf={}'.format(fmt, buf))
        return fmt, buf

    def __get_format(self, fmt_raw, body_raw):
        self.log.debug('fmt_raw={}, body_raw={}'.format(fmt_raw, body_raw))
        if fmt_raw in self.FMT_MAP:
            return self.FMT_MAP[fmt_raw]
        elif fmt_raw in ['Cn']:
            buf = body_raw.read(1)
            n, = struct.unpack(self.e + 'B', buf)
            return str(n) + 's'
        elif fmt_raw in ['Bn']:
            buf = body_raw.read(1)
            n, = struct.unpack(self.e + 'B', buf)
            return str(n) + 'B'
        else:
            raise ValueError

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
