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
import io
from stdf.stdf_reader import Reader

@pytest.fixture()
def rd():
    return Reader('/Users/cahyo/Dropbox/programming/python/STDFReader/tests/stdf_test.json')


def test_read_unsigned(rd):

    r = struct.pack('<HBBBHI', 7, 0x0B, 0x01, 0x81, 0x8001, 0x80000001)
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('T1U', (7, 11, 1),
                 {'UNSIGNED_1': 0x81,
                  'UNSIGNED_2': 0x8001,
                  'UNSIGNED_4': 0x80000001})
    assert not rd.read_record()


def test_read_signed(rd):

    r = struct.pack('<HBBbhi', 7, 0x0B, 0x02, -0x80, -0x8000, -0x80000000)
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('T1I', (7, 11, 2),
                 {'SIGNED_1': -0x80,
                  'SIGNED_2': -0x8000,
                  'SIGNED_4': -0x80000000})
    assert not rd.read_record()


def test_read_float(rd):

    r = struct.pack('<HBBfd', 12, 0x0B, 0x03, 3/2, 22/7)
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('T1F', (12, 11, 3),
                 {'FLOAT': 3/2,
                  'DOUBLE': 22/7})
    assert not rd.read_record()


def test_read_nibble(rd):

    r = struct.pack('<HBBB', 1, 0x0B, 0x04, 0x7D)
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('T1N', (1, 11, 4),
                 {'NIBBLE_1': 0xD,
                  'NIBBLE_2': 0x7})
    assert not rd.read_record()


def test_read_string(rd):

    r = struct.pack('<HBBB5sB7sB11s', 26, 0x0B, 0x05, 5, b'hidup', 7, b'adalah\x00', 11, b'perjuangan\x00')
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('TCn', (26, 11, 5),
                 {'STRING_1': b'hidup',
                  'STRING_2': b'adalah\x00',
                  'STRING_7': b'perjuangan\x00'})
    assert not rd.read_record()


def test_read_seq_of_bytes(rd):

    r = struct.pack('HBBB1BB2BB7B', 13, 0x0B, 0x06, 1, 1, 2, 2, 3, 7, 4, 5, 6, 7, 8, 9, 10)
    rd.STDF_IO = io.BytesIO(r)
    x = rd.read_record()

    assert x == ('TBn', (13, 11, 6),
                 {'BYTE_1': 1,
                  'BYTE_2': (2, 3),
                  'BYTE_7': (4, 5, 6, 7, 8, 9, 10)})
    assert not rd.read_record()