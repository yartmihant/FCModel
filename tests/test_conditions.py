"""Tests for FCLoad, FCRestraint, FCInitialSet and their constants."""
import numpy as np
import pytest

from fc_model import (
    FCModel, FCData, FCLoad, FCRestraint, FCInitialSet,
    FC_LOADS_TYPES_KEYS, FC_LOADS_TYPES_CODES,
    FC_RESTRAINT_FLAGS_KEYS, FC_RESTRAINT_FLAGS_CODES,
    FC_INITIAL_SET_TYPES_KEYS, FC_INITIAL_SET_TYPES_CODES,
)


class TestFCLoadEncodeDecode:
    def _model_with_mesh(self):
        """Helper: create a model with minimal mesh so encode/decode works."""
        from fc_model import FCMesh, FCBlock
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=np.float64)
        from fc_model import FCElement
        m.mesh.add(FCElement({'id':1,'type':'TETRA4','nodes':[1,2,3,4],'parent_id':0,'block':1,'order':1}))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        return m

    def test_roundtrip_via_model(self):
        m = self._model_with_mesh()
        load = m.add_load(
            name="Pressure",
            type="FaceDeadStress",
            apply_to="all",
            data=[FCData.constant(1000.0)],
        )
        assert load.id == 1
        assert load.name == "Pressure"
        assert load.type == "FaceDeadStress"

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert len(m2.loads) == 1
        l2 = m2.loads[0]
        assert l2.name == "Pressure"
        assert l2.type == "FaceDeadStress"

    def test_with_node_ids(self):
        m = self._model_with_mesh()
        load = m.add_load(
            name="Force",
            type="NodeForce",
            apply_to=[1, 2, 3],
            data=[FCData.constant(100.0)] * 6,
        )
        assert len(load.apply) == 3

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert len(m2.loads[0].apply) == 3

    def test_cs_id_preserved(self):
        m = self._model_with_mesh()
        load = m.add_load(
            name="L",
            type="NodeForce",
            apply_to="all",
            cs_id=1,
        )
        assert load.cs_id == 1

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert m2.loads[0].cs_id == 1

    def test_auto_increment_ids(self):
        m = FCModel()
        l1 = m.add_load(name="A", type="NodeForce", apply_to="all")
        l2 = m.add_load(name="B", type="NodeForce", apply_to="all")
        assert l2.id == l1.id + 1


class TestFCRestraintEncodeDecode:
    def _model_with_mesh(self):
        from fc_model import FCBlock, FCElement
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=np.float64)
        m.mesh.add(FCElement({'id':1,'type':'TETRA4','nodes':[1,2,3,4],'parent_id':0,'block':1,'order':1}))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        return m

    def test_roundtrip_via_model(self):
        m = self._model_with_mesh()
        r = m.add_restraint(
            name="Fix",
            flags=["Displacement", "EmptyRestraint", "EmptyRestraint",
                   "EmptyRestraint", "EmptyRestraint", "EmptyRestraint"],
            apply_to="all",
            data=[FCData.constant(0.0)] + [FCData.constant(0.0)] * 5,
        )
        assert r.id == 1
        assert r.flags[0] == "Displacement"

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert len(m2.restraints) == 1
        r2 = m2.restraints[0]
        assert r2.name == "Fix"
        assert r2.flags[0] == "Displacement"

    def test_step_field_preserved(self):
        m = self._model_with_mesh()
        r = m.add_restraint(
            name="R",
            flags=["Temperature"],
            apply_to="all",
            data=[FCData.constant(100.0)],
        )
        r.step = [1, 2, 3]

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert m2.restraints[0].step == [1, 2, 3]

    def test_step_none_not_emitted(self):
        m = self._model_with_mesh()
        m.add_restraint(name="R", flags=["Temperature"], apply_to="all",
                        data=[FCData.constant(0.0)])
        encoded = m.encode()
        assert 'step' not in encoded['restraints'][0]


class TestFCInitialSetEncodeDecode:
    def _model_with_mesh(self):
        from fc_model import FCBlock, FCElement
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=np.float64)
        m.mesh.add(FCElement({'id':1,'type':'TETRA4','nodes':[1,2,3,4],'parent_id':0,'block':1,'order':1}))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        return m

    def test_roundtrip_via_model(self):
        m = self._model_with_mesh()
        init = m.add_initial_set(
            type="Temperature",
            apply_to="all",
            flags=[1],
            data=[FCData.constant(20.0)],
        )
        assert init.id == 1
        assert init.type == "Temperature"
        assert init.flags == [1]

        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert len(m2.initial_sets) == 1
        i2 = m2.initial_sets[0]
        assert i2.type == "Temperature"
        assert i2.flags == [1]

    def test_flags_are_ints(self):
        """Flags must be List[int] (0/1), not mapped through restraint codes."""
        m = self._model_with_mesh()
        init = m.add_initial_set(
            type="Displacement",
            apply_to="all",
            flags=[1, 0, 1, 0, 0, 0],
            data=[FCData.constant(0.0)] * 6,
        )
        assert all(isinstance(f, int) for f in init.flags)

        encoded = m.encode()
        assert encoded['initial_sets'][0]['flag'] == [1, 0, 1, 0, 0, 0]

        m2 = FCModel.decode(encoded)
        assert m2.initial_sets[0].flags == [1, 0, 1, 0, 0, 0]


class TestConditionConstants:
    def test_loads_keys_codes_inverse(self):
        for code, name in FC_LOADS_TYPES_KEYS.items():
            assert FC_LOADS_TYPES_CODES[name] == code

    def test_restraint_flags_inverse(self):
        for code, name in FC_RESTRAINT_FLAGS_KEYS.items():
            assert FC_RESTRAINT_FLAGS_CODES[name] == code

    def test_initial_set_types_inverse(self):
        for code, name in FC_INITIAL_SET_TYPES_KEYS.items():
            assert FC_INITIAL_SET_TYPES_CODES[name] == code

    def test_loads_types_complete(self):
        """Spot-check some known load types."""
        assert FC_LOADS_TYPES_KEYS[1] == "FaceDeadStress"
        assert FC_LOADS_TYPES_KEYS[5] == "NodeForce"
        assert FC_LOADS_TYPES_KEYS[44] == "VolumeGravityMassForce"

    def test_restraint_flags_complete(self):
        assert FC_RESTRAINT_FLAGS_KEYS[0] == "EmptyRestraint"
        assert FC_RESTRAINT_FLAGS_KEYS[1] == "Displacement"
        assert FC_RESTRAINT_FLAGS_KEYS[3] == "Temperature"
