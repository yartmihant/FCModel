"""Tests for FCData — constant, formula, tabular dependencies, encode/decode."""
import numpy as np
import pytest

from fc_model import FCData, FCDependencyColumn, FCValue


class TestFCDataConstant:
    def test_scalar(self):
        d = FCData.constant(42.0)
        assert d.type == "CONSTANT"
        assert d.table == []
        np.testing.assert_array_almost_equal(d.value.data, [42.0])

    def test_int_scalar(self):
        d = FCData.constant(7)
        np.testing.assert_array_almost_equal(d.value.data, [7.0])

    def test_list(self):
        d = FCData.constant([1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(d.value.data, [1.0, 2.0, 3.0])

    def test_empty_table(self):
        d = FCData.constant(0.0)
        assert len(d) == 0  # no table columns → len 0


class TestFCDataFormula:
    def test_formula(self):
        d = FCData.formula("2*x+1")
        assert d.type == "FORMULA"
        assert d.value.type == 'formula'
        assert d.value.data == "2*x+1"
        assert d.table == []


class TestFCDataEncodeDecode:
    def test_constant_roundtrip(self):
        d = FCData.constant(100.0)
        encoded_val, encoded_type, encoded_dep = d.encode()

        d2 = FCData.decode(encoded_val, encoded_type, encoded_dep)
        assert d2.type == "CONSTANT"
        np.testing.assert_array_almost_equal(d2.value.data, [100.0])

    def test_formula_roundtrip(self):
        d = FCData.formula("sin(x)")
        encoded_val, encoded_type, encoded_dep = d.encode()

        d2 = FCData.decode(encoded_val, encoded_type, encoded_dep)
        assert d2.type == "FORMULA"
        assert d2.value.data == "sin(x)"

    def test_tabular_roundtrip(self):
        """Test decode/encode of tabular dependency (type=-1, list of dep columns)."""
        values = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        dep_col = np.array([1.0, 2.0, 3.0], dtype=np.float64)

        val = FCValue(values, 'array')
        col = FCDependencyColumn(type="TABULAR_TEMPERATURE", value=FCValue(dep_col, 'array'))
        d = FCData(val, "TABLE", [col])

        assert len(d) == 3

        encoded_val, encoded_types, encoded_deps = d.encode()
        assert isinstance(encoded_types, list)
        assert encoded_types == [5]  # TABULAR_TEMPERATURE code
        assert isinstance(encoded_deps, list)
        assert len(encoded_deps) == 1

        d2 = FCData.decode(encoded_val, encoded_types, encoded_deps)
        assert d2.type == "TABLE"
        assert len(d2.table) == 1
        assert d2.table[0].type == "TABULAR_TEMPERATURE"
        np.testing.assert_array_almost_equal(d2.value.data, values)
        np.testing.assert_array_almost_equal(d2.table[0].value.data, dep_col)


class TestFCDataRepr:
    def test_constant_repr(self):
        d = FCData.constant(5.0)
        assert "CONST" in repr(d)

    def test_formula_repr(self):
        d = FCData.formula("x^2")
        assert "FORMULA" in repr(d)

    def test_table_repr(self):
        val = FCValue(np.array([1.0], dtype=np.float64), 'array')
        col = FCDependencyColumn(type="TABULAR_TIME", value=FCValue(np.array([0.0], dtype=np.float64), 'array'))
        d = FCData(val, "TABLE", [col])
        assert "TABLE" in repr(d)
