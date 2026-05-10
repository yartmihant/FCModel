"""Tests for FCValue — Base64 encode/decode, formula handling, reshape."""
import numpy as np
import pytest

from fc_model import FCValue


class TestFCValueConstruction:
    def test_array_from_int32(self):
        arr = np.array([1, 2, 3], dtype=np.int32)
        v = FCValue(arr, 'array')
        assert v.type == 'array'
        assert len(v) == 3
        np.testing.assert_array_equal(v.data, arr)

    def test_array_from_float64(self):
        arr = np.array([1.5, 2.5], dtype=np.float64)
        v = FCValue(arr, 'array')
        assert len(v) == 2

    def test_formula(self):
        v = FCValue("all", 'formula')
        assert v.type == 'formula'
        assert v.data == "all"
        assert len(v) == 0  # formulas have zero length

    def test_null(self):
        v = FCValue(np.array([], dtype=np.int32), 'null')
        assert v.type == 'null'
        assert len(v) == 0


class TestFCValueEncodeDecode:
    def test_roundtrip_int32(self):
        arr = np.array([10, 20, 30], dtype=np.int32)
        v = FCValue(arr, 'array')
        encoded = v.encode()
        assert isinstance(encoded, str)

        v2 = FCValue.decode(encoded, np.dtype('int32'))
        assert v2.type == 'array'
        np.testing.assert_array_equal(v2.data, arr)

    def test_roundtrip_float64(self):
        arr = np.array([1.1, 2.2, 3.3], dtype=np.float64)
        v = FCValue(arr, 'array')
        encoded = v.encode()

        v2 = FCValue.decode(encoded, np.dtype('float64'))
        np.testing.assert_array_almost_equal(v2.data, arr)

    def test_decode_empty_string(self):
        v = FCValue.decode("", np.dtype('int32'))
        assert v.type == 'null'
        assert len(v) == 0

    def test_decode_formula_string(self):
        v = FCValue.decode("all", np.dtype('int32'))
        assert v.type == 'formula'
        assert v.data == "all"

    def test_encode_formula(self):
        v = FCValue("sin(x)", 'formula')
        assert v.encode() == "sin(x)"

    def test_decode_explicit_formula_type(self):
        v = FCValue.decode("2*x+1", np.dtype('float64'), 'formula')
        assert v.type == 'formula'
        assert v.data == "2*x+1"


class TestFCValueReshape:
    def test_reshape_2d(self):
        arr = np.array([1, 2, 3, 4, 5, 6], dtype=np.int32)
        v = FCValue(arr, 'array')
        v.reshape(3)
        assert v.data.shape == (3, 2)

    def test_reshape_no_op_when_size_zero(self):
        arr = np.array([1, 2, 3], dtype=np.int32)
        v = FCValue(arr, 'array')
        v.reshape(0)
        assert v.data.shape == (3,)

    def test_reshape_indivisible_no_op(self):
        arr = np.array([1, 2, 3, 4, 5], dtype=np.int32)
        v = FCValue(arr, 'array')
        v.reshape(3)  # 5 % 3 != 0 → no-op
        assert v.data.shape == (5,)
