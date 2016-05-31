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

import pytest
import struct
from stdf.stdf_writer import Writer

@pytest.fixture()
def w():
    return Writer('/Users/cahyo/Dropbox/programming/python/STDFReader/tests/stdf_test.json')


def test_write_unsigned(w):
    data = {
        'UNSIGNED_1': 0x81,
        'UNSIGNED_2': 0x8001,
        'UNSIGNED_4': 0x80000001
    }

    r = w.pack_record('T1U', data)
    u = struct.unpack('<HBBBHI', r)

    assert u == (8, 0x0B, 0x01, 0x81, 0x8001, 0x80000001)


def test_write_signed(w):
    data = {
        'SIGNED_1': -0x80,
        'SIGNED_2': -0x8000,
        'SIGNED_4': -0x80000000
    }

    r = w.pack_record('T1I', data)
    u = struct.unpack('<HBBbhi', r)

    assert u == (8, 0x0B, 0x02, -0x80, -0x8000, -0x80000000)


def test_write_float(w):
    data = {
        'FLOAT': 3/2,
        'DOUBLE': 22/7,
    }

    r = w.pack_record('T1F', data)
    u = struct.unpack('<HBBfd', r)

    assert u == (12, 0x0B, 0x03, 3/2, 22/7)


def test_write_nibble(w):
    data = {
        'NIBBLE_1': 0x0D,
        'NIBBLE_2': 0x07
    }

    r = w.pack_record('T1N', data)
    u = struct.unpack('<HBBB', r)

    assert u == (1, 0x0B, 0x04, 0x7D)


def test_write_string(w):
    data = {
        'STRING_1': ('hidup', 5),
        'STRING_2': ('adalah', 7),
        'STRING_7': ('perjuangan', 11)
    }

    r = w.pack_record('TCn', data)
    u = struct.unpack('<HBBB5sB7sB11s', r)

    assert u == (26, 0x0B, 0x05, 5, b'hidup', 7, b'adalah\x00', 11, b'perjuangan\x00')


def test_write_seq_of_bytes(w):
    data = {
        'BYTE_1': (1,),
        'BYTE_2': (2, 3),
        'BYTE_7': (4, 5, 6, 7, 8, 9, 10)
    }

    r = w.pack_record('TBn', data)
    u = struct.unpack('<HBBB1BB2BB7B', r)

    assert u == (13, 0x0B, 0x06, 1, 1, 2, 2, 3, 7, 4, 5, 6, 7, 8, 9, 10)


def test_write_arrays(w):
    data = {
        'ARR_ICNT': 3,
        'ARR_U1': (0x81, 0x81, 0x81),
        'ARR_U2': (0x8001, 0x8001, 0x8001),
        'ARR_I1': (-0x41, -0x41, -0x41),
        'ARR_I2': (-0x4001, -0x4001, -0x4001),
        'ARR_R4': (3/2, 3/2, 3/2),
        'ARR_R8': (22/7, 22/7, 22/7)
    }

    r = w.pack_record('TA1', data)
    u = struct.unpack('<HBBBBBBHHHbbbhhhfffddd', r)
    assert u[:3] == (60, 0x0B, 7)
    assert u[3] == 3
    assert u[4:7] == (0x81, 0x81, 0x81)
    assert u[7:10] == (0x8001, 0x8001, 0x8001)
    assert u[10:13] == (-0x41, -0x41, -0x41)
    assert u[13:16] == (-0x4001, -0x4001, -0x4001)
    assert u[16:19] == (3/2, 3/2, 3/2)
    assert u[19:] == (22/7, 22/7, 22/7)


def test_write_longer_arrays(w):
    data ={
        'ARR_ICNT': 3,
        'ARR_N1': [0x2, 0x3, 0x5],
        'ARR_Cn': [('hidup', 5), ('adalah', 7), ('perjuangan', 11)],
        'ARR_Bn': [(1,), (2, 3), (4, 5, 6, 7, 8, 9, 10)]
    }

    r = w.pack_record('TA2', data)
    u = struct.unpack('<HBBBBBB5sB7sB11sB1BB2BB7B', r)

    assert u[:3] == (42, 0x0B, 8)
    assert u[3] == 3
    assert u[4:6] == (0x32, 0x05)
    assert u[6:12] == (5, b'hidup', 7, b'adalah\x00', 11, b'perjuangan\x00')
    assert u[12:14] == (1, 1)
    assert u[14:17] == (2, 2, 3)
    assert u[17:] == (7, 4, 5, 6, 7, 8, 9, 10)
