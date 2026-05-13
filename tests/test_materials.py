"""Tests for FCMaterial, FCMaterialProperty, and material constants."""
import numpy as np
import pytest

from fc_model import (
    FCData, FCMaterial, FCMaterialProperty,
    FC_MATERIAL_PROPERTY_NAMES_KEYS, FC_MATERIAL_PROPERTY_NAMES_CODES,
    FC_MATERIAL_PROPERTY_TYPES_KEYS, FC_MATERIAL_PROPERTY_TYPES_CODES,
)


class TestFCMaterialConstruction:
    def test_empty(self):
        m = FCMaterial(id=1, name="Steel")
        assert m.id == 1
        assert m.name == "Steel"
        assert m.properties == {}

    def test_defaults(self):
        m = FCMaterial()
        assert m.id == 0
        assert m.name == ""


class TestFCMaterialAddProperty:
    def test_add_constant_scalar(self):
        m = FCMaterial(id=1, name="Steel")
        prop = m.add_property("common", "DENSITY", 7850.0, "USUAL")
        assert prop.name == "DENSITY"
        assert prop.type == "USUAL"
        assert prop.data.type == "CONSTANT"  # CONSTANT
        np.testing.assert_array_almost_equal(prop.data.value.data, [7850.0])

    def test_add_constant_list(self):
        m = FCMaterial(id=1, name="Mat")
        prop = m.add_property("elasticity", "YOUNG_MODULE", [200e9, 210e9], "HOOK")
        np.testing.assert_array_almost_equal(prop.data.value.data, [200e9, 210e9])

    def test_add_formula(self):
        m = FCMaterial(id=1, name="Mat")
        prop = m.add_property("elasticity", "YOUNG_MODULE", "200e9*(1-T/1000)", "HOOK")
        assert prop.data.type == "FORMULA"  # FORMULA
        assert prop.data.value.data == "200e9*(1-T/1000)"

    def test_add_default_type(self):
        """If property_type is None, default type for the group is used."""
        m = FCMaterial(id=1, name="Mat")
        prop = m.add_property("common", "DENSITY", 1000.0)
        assert prop.type == "USUAL"  # default for common group (code 0)

    def test_grouping_by_type(self):
        """Properties with the same type go into the same sub-list."""
        m = FCMaterial(id=1, name="Mat")
        m.add_property("elasticity", "YOUNG_MODULE", 200e9, "HOOK")
        m.add_property("elasticity", "POISSON_RATIO", 0.3, "HOOK")
        assert len(m.properties["elasticity"]) == 1  # one sub-list
        assert len(m.properties["elasticity"][0]) == 2  # two props in it

    def test_different_types_separate_lists(self):
        m = FCMaterial(id=1, name="Mat")
        m.add_property("elasticity", "YOUNG_MODULE", 200e9, "HOOK")
        m.add_property("elasticity", "C1", 1.0, "COMPR_MOONEY")
        assert len(m.properties["elasticity"]) == 2

    def test_add_list_with_string_raises(self):
        m = FCMaterial(id=1, name="Mat")
        with pytest.raises(TypeError):
            m.add_property("elasticity", "YOUNG_MODULE", [1.0, "bad"], "HOOK")


class TestFCMaterialEncodeDecode:
    def test_roundtrip(self):
        m = FCMaterial(id=5, name="Titanium")
        m.add_property("common", "DENSITY", 4500.0, "USUAL")
        m.add_property("elasticity", "YOUNG_MODULE", 116e9, "HOOK")
        m.add_property("elasticity", "POISSON_RATIO", 0.34, "HOOK")

        encoded = m.encode()
        assert encoded["id"] == 5
        assert encoded["name"] == "Titanium"
        assert "common" in encoded
        assert "elasticity" in encoded

        m2 = FCMaterial.decode(encoded)
        assert m2.id == 5
        assert m2.name == "Titanium"
        assert len(m2.properties["common"]) == 1
        assert len(m2.properties["common"][0]) == 1
        assert m2.properties["common"][0][0].name == "DENSITY"

        assert len(m2.properties["elasticity"]) == 1
        assert len(m2.properties["elasticity"][0]) == 2

    def test_empty_material_roundtrip(self):
        m = FCMaterial(id=1, name="Empty")
        encoded = m.encode()
        m2 = FCMaterial.decode(encoded)
        assert m2.id == 1
        assert m2.name == "Empty"
        assert m2.properties == {}


class TestFCMaterialProperty:
    def test_str(self):
        prop = FCMaterialProperty(type="HOOK", name="YOUNG_MODULE", data=FCData.constant(200e9))
        s = str(prop)
        assert "HOOK" in s
        assert "YOUNG_MODULE" in s

    def test_repr(self):
        prop = FCMaterialProperty(type="USUAL", name="DENSITY", data=FCData.constant(7850.0))
        r = repr(prop)
        assert "USUAL" in r
        assert "DENSITY" in r


class TestMaterialConstants:
    def test_names_keys_codes_inverse(self):
        """NAMES_KEYS and NAMES_CODES should be inverses of each other."""
        for group in FC_MATERIAL_PROPERTY_NAMES_KEYS:
            keys = FC_MATERIAL_PROPERTY_NAMES_KEYS[group]
            codes = FC_MATERIAL_PROPERTY_NAMES_CODES[group]
            for code, name in keys.items():
                assert codes[name] == code, f"{group}: {name} → {code}"

    def test_types_keys_codes_inverse(self):
        for group in FC_MATERIAL_PROPERTY_TYPES_KEYS:
            keys = FC_MATERIAL_PROPERTY_TYPES_KEYS[group]
            codes = FC_MATERIAL_PROPERTY_TYPES_CODES[group]
            for code, name in keys.items():
                assert codes[name] == code, f"{group}: {name} → {code}"

    def test_all_groups_present(self):
        expected = {"elasticity", "common", "thermal", "geomechanic",
                    "plasticity", "hardening", "creep", "preload", "strength", "swelling",
                    "kinematic_hardening", "hsdf"}
        assert set(FC_MATERIAL_PROPERTY_NAMES_KEYS.keys()) == expected
        assert set(FC_MATERIAL_PROPERTY_TYPES_KEYS.keys()) == expected
