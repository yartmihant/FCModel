"""Integration tests for FCModel — construction, load/save, encode/decode."""
import json
from pathlib import Path

import numpy as np
import pytest

from fc_model import (
    FCModel, FCData, FCMaterial, FCBlock, FCSet,
    FCCoordinateSystem, FCConstraint, FCReceiver, FCPropertyTable,
)


class TestFCModelConstruction:
    def test_empty_model(self):
        m = FCModel()
        assert m.header['version'] == 3
        assert len(m.materials) == 0
        assert len(m.loads) == 0
        assert len(m.restraints) == 0
        assert len(m.blocks) == 0
        assert len(m.mesh) == 0
        assert len(m.nodesets) == 0
        assert len(m.sidesets) == 0
        assert m.settings == {}

    def test_default_coordinate_system(self):
        m = FCModel()
        assert 1 in m.coordinate_systems
        cs = m.coordinate_systems[1]
        assert cs.name == "base"
        assert cs.type == "cartesian"


class TestFCModelHelpers:
    def test_add_material(self):
        m = FCModel()
        mat = m.add_material("Steel")
        assert mat.id == 1
        assert mat.name == "Steel"
        assert 1 in m.materials

    def test_add_material_auto_ids(self):
        m = FCModel()
        m.add_material("A")
        m.add_material("B")
        m.add_material("C")
        assert set(m.materials.keys()) == {1, 2, 3}

    def test_add_material_property(self):
        m = FCModel()
        mat = m.add_material("Steel")
        prop = m.add_material_property(mat.id, "common", "DENSITY", 7850.0)
        assert prop.name == "DENSITY"

    def test_add_coordinate_system(self):
        m = FCModel()
        cs = m.add_coordinate_system("custom", "cylindrical")
        assert cs.id == 2  # 1 is base
        assert cs.type == "cylindrical"
        assert 2 in m.coordinate_systems

    def test_add_load(self):
        m = FCModel()
        l = m.add_load("P", "FaceDeadStress", "all", data=[FCData.constant(1.0)])
        assert l.id == 1
        assert len(m.loads) == 1

    def test_add_restraint(self):
        m = FCModel()
        r = m.add_restraint("Fix", flags=["Displacement"] * 3 + ["EmptyRestraint"] * 3,
                            apply_to="all",
                            data=[FCData.constant(0.0)] * 6)
        assert r.id == 1
        assert len(m.restraints) == 1

    def test_add_initial_set(self):
        m = FCModel()
        i = m.add_initial_set("Temperature", "all", flags=[1], data=[FCData.constant(20.0)])
        assert i.id == 1
        assert len(m.initial_sets) == 1

    def test_add_nodeset(self):
        m = FCModel()
        ns = m.add_nodeset("ns1", [1, 2, 3])
        assert ns.id == 1
        assert ns.name == "ns1"
        assert 1 in m.nodesets

    def test_add_sideset(self):
        m = FCModel()
        ss = m.add_sideset("ss1", [1, 1, 2, 1])
        assert ss.id == 1
        assert 1 in m.sidesets


class TestFCModelEncodeDecode:
    def _add_mesh(self, m):
        from fc_model import FCElement, FCBlock
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=np.float64)
        m.mesh.add(FCElement({'id':1,'type':'TETRA4','nodes':[1,2,3,4],'parent_id':0,'block':1,'order':1}))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)

    def test_empty_roundtrip(self):
        m = FCModel()
        self._add_mesh(m)
        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert m2.header['version'] == 3
        assert len(m2.materials) == 0

    def test_full_roundtrip(self):
        """Build a model with all entity types and verify round-trip."""
        m = FCModel()
        self._add_mesh(m)

        # Material
        mat = m.add_material("Steel")
        mat.add_property("common", "DENSITY", 7850.0, "USUAL")
        mat.add_property("elasticity", "YOUNG_MODULE", 200e9, "HOOK")
        mat.add_property("elasticity", "POISSON_RATIO", 0.3, "HOOK")

        # Load, restraint, initial set
        m.add_load("Gravity", "VolumeGravityMassForce", "all",
                    data=[FCData.constant(0.0), FCData.constant(0.0), FCData.constant(-9.81)])
        m.add_restraint("Fix", flags=["Temperature"], apply_to="all",
                        data=[FCData.constant(0.0)])
        m.add_initial_set("Temperature", "all", flags=[1], data=[FCData.constant(20.0)])

        # Sets
        m.add_nodeset("ns", [1, 2])
        m.add_sideset("ss", [1, 1])

        encoded = m.encode()
        m2 = FCModel.decode(encoded)

        assert len(m2.materials) == 1
        assert len(m2.loads) == 1
        assert len(m2.restraints) == 1
        assert len(m2.initial_sets) == 1
        assert len(m2.nodesets) == 1
        assert len(m2.sidesets) == 1

        # Material properties preserved
        mat2 = m2.materials[1]
        assert mat2.name == "Steel"
        assert "common" in mat2.properties
        assert "elasticity" in mat2.properties


class TestFCModelFileIO:
    def test_load_save_simple_cube(self, tmp_path: Path):
        src = Path("tests/data/simple_cube.fc")
        out = tmp_path / "out.fc"

        m = FCModel.load(str(src))
        assert len(m.mesh) > 0
        m.save(str(out))

        with open(out) as f:
            data = json.load(f)
        assert "header" in data
        assert "mesh" in data

    def test_load_save_ultracube_roundtrip(self, tmp_path: Path):
        """Rigorous round-trip: load, save, reload, compare."""
        src = Path("tests/data/ultracube.fc")
        out = tmp_path / "out.fc"

        m = FCModel.load(str(src))
        m.save(str(out))

        with open(src) as f1, open(out) as f2:
            d1 = json.load(f1)
            d2 = json.load(f2)

        assert set(d1.keys()) == set(d2.keys())
        assert d1['header'] == d2['header']
        assert d1['settings'] == d2['settings']


class TestFCModelBlocks:
    def test_block_encode_decode(self):
        b = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)
        encoded = b.encode()
        b2 = FCBlock.decode(encoded)
        assert b2.id == 1
        assert b2.material_id == 1
        assert b2.cs_id == 1

    def test_block_with_steps(self):
        b = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)
        b.steps = [1, 2, 3]
        encoded = b.encode()
        assert encoded['steps'] == [1, 2, 3]
        b2 = FCBlock.decode(encoded)
        assert b2.steps == [1, 2, 3]

    def test_block_with_material_multistep(self):
        b = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)
        b.material = {'ids': [1, 2], 'steps': [1, 2]}
        encoded = b.encode()
        b2 = FCBlock.decode(encoded)
        assert b2.material['ids'] == [1, 2]
        assert b2.material['steps'] == [1, 2]


class TestFCModelConstraints:
    def test_constraint_encode_decode(self):
        c = FCConstraint(id=1, name="contact1", type_val="general")
        c.master = FCModel()._make_apply_value([1, 1, 2, 1])
        c.slave = FCModel()._make_apply_value([3, 1, 4, 1])
        c.properties = {"friction": 0.3, "tolerance": 0.01}

        encoded = c.encode()
        c2 = FCConstraint.decode(encoded)
        assert c2.id == 1
        assert c2.name == "contact1"
        assert c2.type == "general"
        assert c2.properties["friction"] == 0.3


class TestFCModelCoordinateSystem:
    def test_encode_decode(self):
        cs = FCCoordinateSystem(id=1, name="cyl", type_name="cylindrical")
        cs.origin = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        encoded = cs.encode()
        cs2 = FCCoordinateSystem.decode(encoded)
        assert cs2.id == 1
        assert cs2.name == "cyl"
        assert cs2.type == "cylindrical"
        np.testing.assert_array_almost_equal(cs2.origin, [1.0, 2.0, 3.0])


class TestFCModelPropertyTable:
    def test_encode_decode(self):
        pt = FCPropertyTable(id=1, type_val="SHELL", name="shell1")
        pt.properties = {"e": 0.5}
        encoded = pt.encode()
        pt2 = FCPropertyTable.decode(encoded)
        assert pt2.id == 1
        assert pt2.type == "SHELL"
        assert pt2.name == "shell1"
        assert pt2.properties["e"] == 0.5

    def test_name_empty_not_emitted(self):
        pt = FCPropertyTable(id=1, type_val="BEAM")
        encoded = pt.encode()
        assert 'name' not in encoded


class TestFCModelReceiver:
    def test_encode_decode(self):
        r = FCReceiver(id=1, name="recv1", type_val="DISPLACEMENT", dofs=[1, 0, 0, 0, 0, 0])
        r.output_step = 5
        encoded = r.encode()
        r2 = FCReceiver.decode(encoded)
        assert r2.id == 1
        assert r2.name == "recv1"
        assert r2.type == "DISPLACEMENT"
        assert r2.dofs == [1, 0, 0, 0, 0, 0]
        assert r2.output_step == 5

    def test_output_step_none_not_emitted(self):
        r = FCReceiver(id=1, name="r")
        encoded = r.encode()
        assert 'output_step' not in encoded


class TestFCModelSet:
    def test_nodeset_encode_decode(self):
        s = FCSet(id=1, name="ns")
        s.apply = FCModel()._make_apply_value([10, 20, 30])
        encoded = s.encode()
        s2 = FCSet.decode(encoded)
        assert s2.id == 1
        assert s2.name == "ns"
