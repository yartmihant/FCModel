"""Tests for all public constants — verify consistency and completeness."""
from fc_model import (
    FC_DEPENDENCY_TYPES_KEYS, FC_DEPENDENCY_TYPES_CODES,
    FC_LOADS_TYPES_KEYS, FC_LOADS_TYPES_CODES,
    FC_RESTRAINT_FLAGS_KEYS, FC_RESTRAINT_FLAGS_CODES,
    FC_INITIAL_SET_TYPES_KEYS, FC_INITIAL_SET_TYPES_CODES,
    FC_MATERIAL_PROPERTY_NAMES_KEYS, FC_MATERIAL_PROPERTY_NAMES_CODES,
    FC_MATERIAL_PROPERTY_TYPES_KEYS, FC_MATERIAL_PROPERTY_TYPES_CODES,
    FC_ELEMENT_TYPES_KEYID, FC_ELEMENT_TYPES_KEYNAME,
    FC_PROPERTY_TABLE_TYPES_KEYS, FC_PROPERTY_TABLE_TYPES_CODES,
    FC_BEAM_SECTION_TYPES_KEYS, FC_BEAM_SECTION_TYPES_CODES,
    FC_CONTACT_TYPES, FC_CONTACT_METHODS,
    FC_COUPLING_TYPES_KEYS, FC_COUPLING_TYPES_CODES,
    FC_PERIODIC_TYPES_KEYS, FC_PERIODIC_TYPES_CODES,
    FC_RECEIVER_TYPES_KEYS, FC_RECEIVER_TYPES_CODES,
    FC_COORDINATE_SYSTEM_TYPES,
)


class TestDependencyTypes:
    def test_inverse(self):
        for code, name in FC_DEPENDENCY_TYPES_KEYS.items():
            assert FC_DEPENDENCY_TYPES_CODES[name] == code

    def test_known_values(self):
        assert FC_DEPENDENCY_TYPES_KEYS[0] == "CONSTANT"
        assert FC_DEPENDENCY_TYPES_KEYS[6] == "FORMULA"
        assert FC_DEPENDENCY_TYPES_KEYS[5] == "TABULAR_TEMPERATURE"


class TestPropertyTableTypes:
    def test_inverse(self):
        for code, name in FC_PROPERTY_TABLE_TYPES_KEYS.items():
            assert FC_PROPERTY_TABLE_TYPES_CODES[name] == code

    def test_known_values(self):
        assert FC_PROPERTY_TABLE_TYPES_KEYS[0] == "SHELL"
        assert FC_PROPERTY_TABLE_TYPES_KEYS[1] == "BEAM"
        assert FC_PROPERTY_TABLE_TYPES_KEYS[5] == "LUMPMASS"
        assert FC_PROPERTY_TABLE_TYPES_KEYS[6] == "SPRING"


class TestBeamSectionTypes:
    def test_inverse(self):
        for code, name in FC_BEAM_SECTION_TYPES_KEYS.items():
            assert FC_BEAM_SECTION_TYPES_CODES[name] == code

    def test_known_values(self):
        assert FC_BEAM_SECTION_TYPES_KEYS[0] == "RECTANGLE"
        assert FC_BEAM_SECTION_TYPES_KEYS[4] == "POINT"
        assert FC_BEAM_SECTION_TYPES_KEYS[12] == "PIPE"

    def test_count(self):
        assert len(FC_BEAM_SECTION_TYPES_KEYS) == 12  # 0-10 + 12 (no 11)


class TestContactAndCoupling:
    def test_contact_types(self):
        assert "general" in FC_CONTACT_TYPES
        assert "tied" in FC_CONTACT_TYPES
        assert len(FC_CONTACT_TYPES) == 4

    def test_contact_methods(self):
        assert "auto" in FC_CONTACT_METHODS
        assert "penalty" in FC_CONTACT_METHODS
        assert "mpc" in FC_CONTACT_METHODS

    def test_coupling_inverse(self):
        for code, name in FC_COUPLING_TYPES_KEYS.items():
            assert FC_COUPLING_TYPES_CODES[name] == code

    def test_coupling_known(self):
        assert FC_COUPLING_TYPES_KEYS[0] == "ELASTICITY"
        assert FC_COUPLING_TYPES_KEYS[5] == "INTERPOLATION"

    def test_periodic_inverse(self):
        for code, name in FC_PERIODIC_TYPES_KEYS.items():
            assert FC_PERIODIC_TYPES_CODES[name] == code

    def test_periodic_known(self):
        assert FC_PERIODIC_TYPES_KEYS[0] == "ALL"
        assert FC_PERIODIC_TYPES_KEYS[5] == "ACCELERATION"


class TestReceiverTypes:
    def test_inverse(self):
        for code, name in FC_RECEIVER_TYPES_KEYS.items():
            assert FC_RECEIVER_TYPES_CODES[name] == code

    def test_known(self):
        assert FC_RECEIVER_TYPES_KEYS[0] == "DISPLACEMENT"
        assert FC_RECEIVER_TYPES_KEYS[3] == "PRESSURE"


class TestCoordinateSystemTypes:
    def test_known(self):
        assert "cartesian" in FC_COORDINATE_SYSTEM_TYPES
        assert "cylindrical" in FC_COORDINATE_SYSTEM_TYPES
        assert "spherical" in FC_COORDINATE_SYSTEM_TYPES
        assert len(FC_COORDINATE_SYSTEM_TYPES) == 3


class TestElementTypesCompleteness:
    def test_all_spec_solid_fem(self):
        """All solid FEM element types from spec must be present."""
        expected = {
            'TETRA4': 1, 'TETRA10': 2, 'HEX8': 3, 'HEX20': 4,
            'WEDGE6': 6, 'WEDGE15': 7, 'PYR5': 8, 'PYR13': 9,
            'TRI3': 10, 'TRI6': 11, 'QUAD4': 12, 'QUAD8': 13,
        }
        for name, code in expected.items():
            assert name in FC_ELEMENT_TYPES_KEYNAME, f"Missing {name}"
            assert FC_ELEMENT_TYPES_KEYNAME[name]['code'] == code

    def test_all_spec_solid_sem(self):
        expected = {
            'TETRA4S': 15, 'TETRA10S': 16, 'HEX8S': 17, 'HEX20S': 18,
            'WEDGE6S': 20, 'WEDGE15S': 21, 'PYR5S': 22, 'PYR13S': 23,
            'TRI3S': 24, 'TRI6S': 25, 'QUAD4S': 26, 'QUAD8S': 27,
        }
        for name, code in expected.items():
            assert name in FC_ELEMENT_TYPES_KEYNAME, f"Missing {name}"
            assert FC_ELEMENT_TYPES_KEYNAME[name]['code'] == code

    def test_all_spec_shell(self):
        expected = {
            'MITC3': 29, 'MITC6': 30, 'MITC4': 31, 'MITC8': 32,
            'SHELL3S': 84, 'SHELL4S': 85, 'SHELL6S': 86, 'SHELL8S': 87,
        }
        for name, code in expected.items():
            assert name in FC_ELEMENT_TYPES_KEYNAME, f"Missing {name}"
            assert FC_ELEMENT_TYPES_KEYNAME[name]['code'] == code

    def test_all_spec_beam_spring_mass(self):
        expected = {
            'BEAM26': 36, 'BEAM36': 37, 'SPRING3D': 39, 'SPRING6D': 41,
            'SPRING2D': 83, 'BEAM27': 89, 'BEAM37': 90,
            'BEAM26S': 95, 'BEAM36S': 96, 'BEAM27S': 97, 'BEAM37S': 98,
            'LUMPMASS3D': 38, 'LUMPMASS6D': 40, 'LUMPMASS2D': 82,
            'POINT3D': 99, 'POINT2D': 100, 'POINT6D': 101, 'LUMPMASS2DR': 105,
        }
        for name, code in expected.items():
            assert name in FC_ELEMENT_TYPES_KEYNAME, f"Missing {name}"
            assert FC_ELEMENT_TYPES_KEYNAME[name]['code'] == code

    def test_node_count_positive(self):
        """All element types must have nodes_count > 0 (except NONE)."""
        for name, info in FC_ELEMENT_TYPES_KEYNAME.items():
            if name == 'NONE':
                assert info['nodes_count'] == 0
            else:
                assert info['nodes_count'] > 0, f"{name} has 0 nodes"


class TestLoadTypesCompleteness:
    def test_face_loads(self):
        face = {1, 3, 11, 13, 15, 19, 21, 22, 23, 24, 25, 26, 35, 36, 37, 38, 39}
        for code in face:
            assert code in FC_LOADS_TYPES_KEYS

    def test_segment_loads(self):
        seg = {2, 4, 12, 14, 16, 20, 31, 32, 33, 34, 40}
        for code in seg:
            assert code in FC_LOADS_TYPES_KEYS

    def test_node_loads(self):
        node = {5, 18, 28, 29, 30, 41, 43}
        for code in node:
            assert code in FC_LOADS_TYPES_KEYS

    def test_volume_loads(self):
        vol = {17, 42, 44}
        for code in vol:
            assert code in FC_LOADS_TYPES_KEYS
