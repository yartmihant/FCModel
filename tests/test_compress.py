"""Tests for FCModel.compress() — index space normalization."""
import json
from pathlib import Path
from typing import List

import numpy as np
import pytest

from fc_model import (
    FCModel, FCBlock, FCConstraint, FCData, FCDependencyColumn,
    FCElement, FCMaterial, FCMaterialProperty,
    FCPropertyTable, FCReceiver, FCSet, FCValue,
    FCCoordinateSystem,
)


def _make_model_with_gaps() -> FCModel:
    """Build a model with non-contiguous IDs across all entity types."""
    m = FCModel()

    # Coordinate systems: base=1 exists, add more with gaps
    cs2 = m.add_coordinate_system("cyl", "cylindrical")  # id=2
    cs3 = m.add_coordinate_system("sph", "spherical")     # id=3
    # Artificially create gap: remove cs2, add cs with id=5
    del m.coordinate_systems[2]
    cs5 = FCCoordinateSystem(id=5, name="gap_cs", type_name="cartesian")
    m.coordinate_systems[5] = cs5

    # Materials with gap: ids 3, 7
    mat3 = FCMaterial(id=3, name="Steel")
    m.materials[3] = mat3
    mat7 = FCMaterial(id=7, name="Aluminum")
    m.materials[7] = mat7

    # Property tables with gap: ids 2, 10
    pt2 = FCPropertyTable(id=2, type_val=0, name="Shell1")
    m.property_tables[2] = pt2
    pt10 = FCPropertyTable(id=10, type_val=1, name="Beam1")
    m.property_tables[10] = pt10

    # Blocks with gap: ids 5, 15
    blk5 = FCBlock(id=5, cs_id=5, material_id=3, property_id=2)
    blk15 = FCBlock(id=15, cs_id=1, material_id=7, property_id=10)
    blk15.material = {'ids': [3, 7], 'steps': [1, 2]}
    m.blocks[5] = blk5
    m.blocks[15] = blk15

    # Mesh nodes with gap: ids 10, 20, 30, 40
    m.mesh.nodes_ids = np.array([10, 20, 30, 40], dtype=np.int32)
    m.mesh.nodes_xyz = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
    ], dtype=np.float64)

    # Elements with gap: ids 100, 200, referencing blocks 5, 15
    m.mesh.add(FCElement({
        'id': 100, 'type': 'TETRA4', 'nodes': [10, 20, 30, 40],
        'parent_id': 0, 'block': 5, 'order': 1,
    }))
    m.mesh.add(FCElement({
        'id': 200, 'type': 'TETRA4', 'nodes': [10, 20, 30, 40],
        'parent_id': 100, 'block': 15, 'order': 1,
    }))

    # Load referencing node IDs and cs
    load = m.add_load("P", "FaceDeadStress", [10, 20, 30], cs_id=5,
                       data=[FCData.constant(1.0)])
    load.id = 5

    # Restraint referencing node IDs
    rest = m.add_restraint("Fix", flags=["Displacement"], apply_to=[20, 40], cs_id=1,
                            data=[FCData.constant(0.0)])
    rest.id = 10

    # Initial set
    init = m.add_initial_set("Temperature", [10, 30], cs_id=5,
                              flags=[1], data=[FCData.constant(20.0)])
    init.id = 7

    # Contact constraint
    cc = FCConstraint(id=5, name="contact1", type_val="general")
    cc.master = FCValue(np.array([10, 20], dtype=np.int32))
    cc.slave = FCValue(np.array([30, 40], dtype=np.int32))
    m.contact_constraints.append(cc)

    # Receiver
    rcv = FCReceiver(id=8, name="rcv1", type_val=0, dofs=[1, 2, 3])
    rcv.apply = FCValue(np.array([10, 30], dtype=np.int32))
    m.receivers.append(rcv)

    # Nodeset with gap
    ns = FCSet(id=5, name="ns_gap")
    ns.apply = FCValue(np.array([10, 20, 40], dtype=np.int32))
    m.nodesets[5] = ns

    # Sideset with gap: pairs [elem_id, face_idx]
    ss = FCSet(id=10, name="ss_gap")
    ss.apply = FCValue(np.array([100, 1, 200, 2], dtype=np.int32))
    ss.apply.reshape(2)
    m.sidesets[10] = ss

    return m


class TestCompressBasic:
    def test_compress_empty_model(self):
        m = FCModel()
        m.compress()
        assert 1 in m.coordinate_systems

    def test_compress_already_canonical(self):
        """If IDs are already [1,2,3...], compress is a no-op."""
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((4, 3), dtype=np.float64)
        m.mesh.add(FCElement({
            'id': 1, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)
        mat = m.add_material("M")
        m.compress()
        assert list(m.coordinate_systems.keys()) == [1]
        assert list(m.materials.keys()) == [1]
        assert list(m.blocks.keys()) == [1]
        np.testing.assert_array_equal(m.mesh.nodes_ids, [1, 2, 3, 4])


class TestCompressCoordinateSystems:
    def test_cs_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.coordinate_systems.keys()) == [1, 2, 3]
        assert m.coordinate_systems[1].name == "base"
        assert m.coordinate_systems[2].name == "sph"
        assert m.coordinate_systems[3].name == "gap_cs"

    def test_cs_refs_updated_in_blocks(self):
        m = _make_model_with_gaps()
        m.compress()
        # blk5 had cs_id=5, now cs 5 -> 3
        blk1 = m.blocks[1]
        assert blk1.cs_id == 3

    def test_cs_refs_updated_in_load(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.loads[0].cs_id == 3  # was 5

    def test_cs_refs_updated_in_restraint(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.restraints[0].cs_id == 1  # was 1 (unchanged)

    def test_cs_refs_updated_in_initial_set(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.initial_sets[0].cs_id == 3  # was 5


class TestCompressMaterials:
    def test_materials_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.materials.keys()) == [1, 2]
        assert m.materials[1].name == "Steel"
        assert m.materials[2].name == "Aluminum"

    def test_material_refs_in_blocks(self):
        m = _make_model_with_gaps()
        m.compress()
        # blk5 had material_id=3 -> now 1
        assert m.blocks[1].material_id == 1
        # blk15 had material_id=7 -> now 2
        assert m.blocks[2].material_id == 2

    def test_material_multistep_refs(self):
        m = _make_model_with_gaps()
        m.compress()
        # blk15 had material.ids=[3,7] -> [1,2]
        assert m.blocks[2].material is not None
        assert m.blocks[2].material['ids'] == [1, 2]


class TestCompressPropertyTables:
    def test_pt_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.property_tables.keys()) == [1, 2]

    def test_pt_refs_in_blocks(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.blocks[1].property_id == 1  # was 2
        assert m.blocks[2].property_id == 2  # was 10


class TestCompressBlocks:
    def test_blocks_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.blocks.keys()) == [1, 2]

    def test_element_block_refs(self):
        m = _make_model_with_gaps()
        m.compress()
        for elem in m.mesh:
            assert elem.block in [1, 2]


class TestCompressNodes:
    def test_nodes_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        np.testing.assert_array_equal(m.mesh.nodes_ids, [1, 2, 3, 4])

    def test_element_nodes_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        for elem in m.mesh:
            for n in elem.nodes:
                assert 1 <= n <= 4

    def test_load_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        load = m.loads[0]
        assert load.apply.type == 'array'
        data = load.apply.data
        assert isinstance(data, np.ndarray)
        # [10,20,30] -> [1,2,3]
        np.testing.assert_array_equal(data.ravel(), [1, 2, 3])

    def test_restraint_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        rest = m.restraints[0]
        data = rest.apply.data
        assert isinstance(data, np.ndarray)
        # [20,40] -> [2,4]
        np.testing.assert_array_equal(data.ravel(), [2, 4])

    def test_initial_set_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        init = m.initial_sets[0]
        data = init.apply.data
        assert isinstance(data, np.ndarray)
        np.testing.assert_array_equal(data.ravel(), [1, 3])

    def test_constraint_master_slave_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        cc = m.contact_constraints[0]
        np.testing.assert_array_equal(np.asarray(cc.master.data).ravel(), [1, 2])
        np.testing.assert_array_equal(np.asarray(cc.slave.data).ravel(), [3, 4])

    def test_receiver_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        rcv = m.receivers[0]
        np.testing.assert_array_equal(np.asarray(rcv.apply.data).ravel(), [1, 3])

    def test_nodeset_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        ns = list(m.nodesets.values())[0]
        np.testing.assert_array_equal(np.asarray(ns.apply.data).ravel(), [1, 2, 4])

    def test_xyz_preserved(self):
        m = _make_model_with_gaps()
        original_xyz = m.mesh.nodes_xyz.copy()
        m.compress()
        np.testing.assert_array_equal(m.mesh.nodes_xyz, original_xyz)


class TestCompressElements:
    def test_elements_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        elem_ids = sorted(e.id for e in m.mesh)
        assert elem_ids == [1, 2]

    def test_parent_id_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        elems = list(m.mesh)
        # elem 200 had parent_id=100 -> now parent_id should be 1
        parent_ids = {e.id: e.parent_id for e in elems}
        # elem with new id=1 (was 100) has parent_id=0
        assert parent_ids[1] == 0
        # elem with new id=2 (was 200) has parent_id=1
        assert parent_ids[2] == 1

    def test_sideset_apply_remapped(self):
        m = _make_model_with_gaps()
        m.compress()
        ss = list(m.sidesets.values())[0]
        data = np.asarray(ss.apply.data)
        # Original: [[100, 1], [200, 2]] -> [[1, 1], [2, 2]]
        assert data.shape == (2, 2)
        np.testing.assert_array_equal(data[:, 0], [1, 2])  # elem_ids remapped
        np.testing.assert_array_equal(data[:, 1], [1, 2])  # face_idx unchanged


class TestCompressAutonomousIDs:
    def test_load_ids(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.loads[0].id == 1

    def test_restraint_ids(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.restraints[0].id == 1

    def test_initial_set_ids(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.initial_sets[0].id == 1

    def test_constraint_ids(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.contact_constraints[0].id == 1

    def test_receiver_ids(self):
        m = _make_model_with_gaps()
        m.compress()
        assert m.receivers[0].id == 1


class TestCompressSets:
    def test_nodeset_keys_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.nodesets.keys()) == [1]
        assert m.nodesets[1].id == 1
        assert m.nodesets[1].name == "ns_gap"

    def test_sideset_keys_reindexed(self):
        m = _make_model_with_gaps()
        m.compress()
        assert list(m.sidesets.keys()) == [1]
        assert m.sidesets[1].id == 1
        assert m.sidesets[1].name == "ss_gap"


class TestCompressFormulaApply:
    def test_formula_apply_not_changed(self):
        """When apply is a formula (e.g. 'all'), compress should not crash."""
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((2, 3), dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        load = m.add_load("P", "NodeForce", "all", data=[FCData.constant(1.0)])
        m.compress()
        assert load.apply.type == 'formula'
        assert load.apply.data == 'all'


class TestCompressRoundTrip:
    def test_compress_then_encode_decode(self):
        """Compress + encode/decode should produce a valid model."""
        m = _make_model_with_gaps()
        m.compress()
        encoded = m.encode()
        m2 = FCModel.decode(encoded)
        assert list(m2.coordinate_systems.keys()) == [1, 2, 3]
        assert list(m2.materials.keys()) == [1, 2]
        assert list(m2.blocks.keys()) == [1, 2]
        np.testing.assert_array_equal(m2.mesh.nodes_ids, [1, 2, 3, 4])

    def test_compress_real_file(self, tmp_path: Path):
        """Load a real .fc file, compress, save, reload and verify canonical IDs."""
        src = Path("tests/data/simple_cube.fc")
        if not src.exists():
            pytest.skip("Test data not available")
        m = FCModel.load(str(src))
        m.compress()
        out = tmp_path / "compressed.fc"
        m.save(str(out))
        m2 = FCModel.load(str(out))

        # All IDs should be 1-based sequential
        assert list(m2.coordinate_systems.keys()) == list(range(1, len(m2.coordinate_systems) + 1))
        if m2.materials:
            assert list(m2.materials.keys()) == list(range(1, len(m2.materials) + 1))
        if m2.blocks:
            assert list(m2.blocks.keys()) == list(range(1, len(m2.blocks) + 1))
        if len(m2.mesh.nodes_ids) > 0:
            np.testing.assert_array_equal(
                m2.mesh.nodes_ids,
                np.arange(1, len(m2.mesh.nodes_ids) + 1, dtype=np.int32)
            )

    def test_idempotent(self):
        """Calling compress twice should produce the same result."""
        m = _make_model_with_gaps()
        m.compress()
        enc1 = json.dumps(m.encode(), sort_keys=True)
        m.compress()
        enc2 = json.dumps(m.encode(), sort_keys=True)
        assert enc1 == enc2


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------

class TestCompressCouplingPeriodicConstraints:
    def test_coupling_constraint_remapped(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20, 30], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((3, 3), dtype=np.float64)

        cc = FCConstraint(id=5, name="coup", type_val=0)
        cc.master = FCValue(np.array([10], dtype=np.int32))
        cc.slave = FCValue(np.array([20, 30], dtype=np.int32))
        m.coupling_constraints.append(cc)
        m.compress()

        assert m.coupling_constraints[0].id == 1
        np.testing.assert_array_equal(np.asarray(cc.master.data).ravel(), [1])
        np.testing.assert_array_equal(np.asarray(cc.slave.data).ravel(), [2, 3])

    def test_periodic_constraint_remapped(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([50, 60], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((2, 3), dtype=np.float64)

        pc = FCConstraint(id=9, name="per", type_val=0)
        pc.master = FCValue(np.array([50], dtype=np.int32))
        pc.slave = FCValue(np.array([60], dtype=np.int32))
        m.periodic_constraints.append(pc)
        m.compress()

        assert m.periodic_constraints[0].id == 1
        np.testing.assert_array_equal(np.asarray(pc.master.data).ravel(), [1])
        np.testing.assert_array_equal(np.asarray(pc.slave.data).ravel(), [2])


class TestCompressMultipleAutonomous:
    def test_multiple_loads_renumbered(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([1], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((1, 3), dtype=np.float64)
        l1 = m.add_load("A", "NodeForce", "all", data=[FCData.constant(1.0)])
        l2 = m.add_load("B", "NodeForce", "all", data=[FCData.constant(2.0)])
        l3 = m.add_load("C", "NodeForce", "all", data=[FCData.constant(3.0)])
        l1.id = 10
        l2.id = 20
        l3.id = 30
        m.compress()
        assert [l.id for l in m.loads] == [1, 2, 3]
        assert [l.name for l in m.loads] == ["A", "B", "C"]

    def test_multiple_restraints_renumbered(self):
        m = FCModel()
        r1 = m.add_restraint("R1", flags=["Displacement"], apply_to="all",
                              data=[FCData.constant(0.0)])
        r2 = m.add_restraint("R2", flags=["Temperature"], apply_to="all",
                              data=[FCData.constant(20.0)])
        r1.id = 100
        r2.id = 200
        m.compress()
        assert [r.id for r in m.restraints] == [1, 2]

    def test_multiple_initial_sets_renumbered(self):
        m = FCModel()
        i1 = m.add_initial_set("Temperature", "all", flags=[1],
                                data=[FCData.constant(20.0)])
        i2 = m.add_initial_set("Displacement", "all", flags=[0],
                                data=[FCData.constant(0.0)])
        i1.id = 50
        i2.id = 60
        m.compress()
        assert [i.id for i in m.initial_sets] == [1, 2]

    def test_multiple_receivers_renumbered(self):
        m = FCModel()
        r1 = FCReceiver(id=7, name="r1", type_val=0, dofs=[1])
        r1.apply = FCValue(np.array([], dtype=np.int32))
        r2 = FCReceiver(id=13, name="r2", type_val=0, dofs=[2])
        r2.apply = FCValue(np.array([], dtype=np.int32))
        m.receivers = [r1, r2]
        m.compress()
        assert [r.id for r in m.receivers] == [1, 2]


class TestCompressTabularData:
    def _make_model_with_tabular_node_data(self) -> FCModel:
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20, 30], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((3, 3), dtype=np.float64)

        # Material with TABULAR_NODE_ID property
        mat = m.add_material("TabMat")
        node_id_col = FCDependencyColumn(
            type="TABULAR_NODE_ID",
            value=FCValue(np.array([10.0, 20.0, 30.0], dtype=np.float64))
        )
        value_col = FCValue(np.array([100.0, 200.0, 300.0], dtype=np.float64))
        tabular_data = FCData(value_col, -1, [node_id_col])
        prop = FCMaterialProperty(type="HOOK", name="YOUNG_MODULE", data=tabular_data)
        mat.properties["elasticity"] = [[prop]]

        return m

    def _make_model_with_tabular_element_data(self) -> FCModel:
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((4, 3), dtype=np.float64)
        m.mesh.add(FCElement({
            'id': 50, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)
        mat = m.add_material("TabMat")

        elem_id_col = FCDependencyColumn(
            type="TABULAR_ELEMENT_ID",
            value=FCValue(np.array([50.0], dtype=np.float64))
        )
        value_col = FCValue(np.array([999.0], dtype=np.float64))
        tabular_data = FCData(value_col, -1, [elem_id_col])
        prop = FCMaterialProperty(type="HOOK", name="YOUNG_MODULE", data=tabular_data)
        mat.properties["elasticity"] = [[prop]]

        return m

    def test_tabular_node_id_remapped(self):
        m = self._make_model_with_tabular_node_data()
        m.compress()
        mat = m.materials[1]
        prop = mat.properties["elasticity"][0][0]
        col = prop.data.table[0]
        assert col.type == "TABULAR_NODE_ID"
        np.testing.assert_array_equal(
            np.asarray(col.value.data).ravel(), [1.0, 2.0, 3.0]
        )

    def test_tabular_element_id_remapped(self):
        m = self._make_model_with_tabular_element_data()
        m.compress()
        mat = m.materials[1]
        prop = mat.properties["elasticity"][0][0]
        col = prop.data.table[0]
        assert col.type == "TABULAR_ELEMENT_ID"
        # elem 50 -> 1
        np.testing.assert_array_equal(
            np.asarray(col.value.data).ravel(), [1.0]
        )

    def test_tabular_node_id_in_load(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([5, 15], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((2, 3), dtype=np.float64)

        node_col = FCDependencyColumn(
            type="TABULAR_NODE_ID",
            value=FCValue(np.array([5.0, 15.0], dtype=np.float64))
        )
        value_fcv = FCValue(np.array([1.0, 2.0], dtype=np.float64))
        tab_data = FCData(value_fcv, -1, [node_col])

        load = m.add_load("P", "NodeForce", "all", data=[tab_data])
        m.compress()

        col = m.loads[0].data[0].table[0]
        np.testing.assert_array_equal(
            np.asarray(col.value.data).ravel(), [1.0, 2.0]
        )

    def test_constant_data_not_affected(self):
        """Non-tabular FCData should not be modified by compress."""
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((2, 3), dtype=np.float64)
        load = m.add_load("P", "NodeForce", "all", data=[FCData.constant(42.0)])
        m.compress()
        val = np.asarray(m.loads[0].data[0].value.data).ravel()
        np.testing.assert_array_equal(val, [42.0])


class TestCompressMultipleElementTypes:
    def test_mixed_element_types(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20, 30, 40, 50, 60, 70, 80],
                                     dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((8, 3), dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)

        m.mesh.add(FCElement({
            'id': 100, 'type': 'TETRA4', 'nodes': [10, 20, 30, 40],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.mesh.add(FCElement({
            'id': 200, 'type': 'HEX8',
            'nodes': [10, 20, 30, 40, 50, 60, 70, 80],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.compress()

        elem_ids = sorted(e.id for e in m.mesh)
        assert elem_ids == [1, 2]
        types = {e.id: e.type for e in m.mesh}
        assert types[1] == 'TETRA4'
        assert types[2] == 'HEX8'
        # Nodes should be 1..8
        for e in m.mesh:
            for n in e.nodes:
                assert 1 <= n <= 8

    def test_element_order_preserved(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((3, 3), dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        m.mesh.add(FCElement({
            'id': 50, 'type': 'TRI3', 'nodes': [1, 2, 3],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.compress()
        elem = list(m.mesh)[0]
        assert elem.order == 1
        assert elem.type == 'TRI3'


class TestCompressEmptyCollections:
    def test_no_materials(self):
        m = FCModel()
        m.compress()
        assert m.materials == {}

    def test_no_blocks(self):
        m = FCModel()
        m.compress()
        assert m.blocks == {}

    def test_no_property_tables(self):
        m = FCModel()
        m.compress()
        assert m.property_tables == {}

    def test_no_loads_restraints_initial_sets(self):
        m = FCModel()
        m.compress()
        assert m.loads == []
        assert m.restraints == []
        assert m.initial_sets == []

    def test_no_constraints(self):
        m = FCModel()
        m.compress()
        assert m.contact_constraints == []
        assert m.coupling_constraints == []
        assert m.periodic_constraints == []

    def test_no_receivers(self):
        m = FCModel()
        m.compress()
        assert m.receivers == []

    def test_no_nodesets_sidesets(self):
        m = FCModel()
        m.compress()
        assert m.nodesets == {}
        assert m.sidesets == {}

    def test_empty_apply_array(self):
        """FCValue with empty ndarray should not crash."""
        m = FCModel()
        rcv = FCReceiver(id=3, name="empty", type_val=0, dofs=[])
        rcv.apply = FCValue(np.array([], dtype=np.int32))
        m.receivers.append(rcv)
        m.compress()
        assert m.receivers[0].id == 1
        assert np.asarray(m.receivers[0].apply.data).size == 0


class TestCompressMultipleSets:
    def test_multiple_nodesets(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20, 30], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((3, 3), dtype=np.float64)

        ns1 = FCSet(id=5, name="A")
        ns1.apply = FCValue(np.array([10, 20], dtype=np.int32))
        ns2 = FCSet(id=10, name="B")
        ns2.apply = FCValue(np.array([30], dtype=np.int32))
        m.nodesets = {5: ns1, 10: ns2}

        m.compress()
        assert list(m.nodesets.keys()) == [1, 2]
        assert m.nodesets[1].name == "A"
        assert m.nodesets[2].name == "B"
        np.testing.assert_array_equal(np.asarray(m.nodesets[1].apply.data).ravel(), [1, 2])
        np.testing.assert_array_equal(np.asarray(m.nodesets[2].apply.data).ravel(), [3])

    def test_multiple_sidesets(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((4, 3), dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        m.mesh.add(FCElement({
            'id': 50, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.mesh.add(FCElement({
            'id': 80, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))

        ss1 = FCSet(id=7, name="S1")
        ss1.apply = FCValue(np.array([50, 0, 80, 1], dtype=np.int32))
        ss1.apply.reshape(2)
        ss2 = FCSet(id=12, name="S2")
        ss2.apply = FCValue(np.array([80, 2], dtype=np.int32))
        ss2.apply.reshape(1)
        m.sidesets = {7: ss1, 12: ss2}

        m.compress()
        assert list(m.sidesets.keys()) == [1, 2]
        d1 = np.asarray(m.sidesets[1].apply.data)
        assert d1.shape == (2, 2)
        np.testing.assert_array_equal(d1[:, 0], [1, 2])  # elem 50->1, 80->2
        d2 = np.asarray(m.sidesets[2].apply.data)
        np.testing.assert_array_equal(d2.ravel()[0], 2)  # elem 80->2


class TestCompressCsIdZero:
    def test_cs_id_zero_unchanged(self):
        """cs_id=0 means 'no coordinate system' and should stay 0."""
        m = FCModel()
        blk = FCBlock(id=5, cs_id=0, material_id=0, property_id=0)
        m.blocks[5] = blk
        load = m.add_load("P", "NodeForce", "all", data=[FCData.constant(1.0)])
        load.cs_id = 0
        m.compress()
        assert m.blocks[1].cs_id == 0
        assert m.loads[0].cs_id == 0


class TestCompressParentIdZero:
    def test_parent_id_zero_stays_zero(self):
        m = FCModel()
        m.mesh.nodes_ids = np.array([10, 20, 30, 40], dtype=np.int32)
        m.mesh.nodes_xyz = np.zeros((4, 3), dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        m.mesh.add(FCElement({
            'id': 50, 'type': 'TETRA4', 'nodes': [10, 20, 30, 40],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.compress()
        assert list(m.mesh)[0].parent_id == 0


class TestCompressRealFiles:
    def test_ultracube_compress_roundtrip(self, tmp_path: Path):
        src = Path("tests/data/ultracube.fc")
        if not src.exists():
            pytest.skip("Test data not available")
        m = FCModel.load(str(src))
        n_elems_before = len(m.mesh)
        n_nodes_before = len(m.mesh.nodes_ids)
        n_mats = len(m.materials)
        n_blocks = len(m.blocks)

        m.compress()

        assert len(m.mesh) == n_elems_before
        assert len(m.mesh.nodes_ids) == n_nodes_before
        assert len(m.materials) == n_mats
        assert len(m.blocks) == n_blocks

        # Sequential IDs
        np.testing.assert_array_equal(
            m.mesh.nodes_ids,
            np.arange(1, n_nodes_before + 1, dtype=np.int32)
        )
        elem_ids = sorted(e.id for e in m.mesh)
        assert elem_ids == list(range(1, n_elems_before + 1))

        # Save/reload
        out = tmp_path / "compressed_ultra.fc"
        m.save(str(out))
        m2 = FCModel.load(str(out))
        assert len(m2.mesh) == n_elems_before

    def test_cube_sidesets_compress_roundtrip(self, tmp_path: Path):
        src = Path("tests/data/cube_sidesets.fc")
        if not src.exists():
            pytest.skip("Test data not available")
        m = FCModel.load(str(src))
        n_ss = len(m.sidesets)

        m.compress()

        assert len(m.sidesets) == n_ss
        assert list(m.sidesets.keys()) == list(range(1, n_ss + 1))
        for ss in m.sidesets.values():
            if ss.apply.type == 'array' and isinstance(ss.apply.data, np.ndarray):
                data = ss.apply.data
                if data.ndim == 2:
                    for eid in data[:, 0]:
                        assert int(eid) >= 1

        out = tmp_path / "compressed_ss.fc"
        m.save(str(out))
        m2 = FCModel.load(str(out))
        assert len(m2.sidesets) == n_ss

    def test_all_fc_files_compress_without_error(self, tmp_path: Path):
        """Every .fc file in tests/data/ should survive compress + roundtrip."""
        data_dir = Path("tests/data")
        fc_files = sorted(data_dir.glob("*.fc"))
        assert len(fc_files) > 0, "No .fc test files found"
        for fc_path in fc_files:
            m = FCModel.load(str(fc_path))
            m.compress()
            out = tmp_path / fc_path.name
            m.save(str(out))
            m2 = FCModel.load(str(out))
            assert len(m2.mesh) == len(m.mesh), f"Element count mismatch for {fc_path.name}"


class TestCompressDataIntegrity:
    def test_node_xyz_order_matches_new_ids(self):
        """After compress, xyz[i] should correspond to nodes_ids[i]."""
        m = FCModel()
        m.mesh.nodes_ids = np.array([30, 10, 20], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([
            [3.0, 0, 0],  # node 30
            [1.0, 0, 0],  # node 10
            [2.0, 0, 0],  # node 20
        ], dtype=np.float64)
        m.compress()
        # IDs become [1,2,3] but xyz order is unchanged
        np.testing.assert_array_equal(m.mesh.nodes_ids, [1, 2, 3])
        np.testing.assert_array_equal(m.mesh.nodes_xyz[0], [3.0, 0, 0])
        np.testing.assert_array_equal(m.mesh.nodes_xyz[1], [1.0, 0, 0])
        np.testing.assert_array_equal(m.mesh.nodes_xyz[2], [2.0, 0, 0])

    def test_element_node_connectivity_preserved(self):
        """After compress, elements should reference the same physical nodes."""
        m = FCModel()
        m.mesh.nodes_ids = np.array([100, 200, 300], dtype=np.int32)
        m.mesh.nodes_xyz = np.array([
            [10.0, 0, 0],
            [20.0, 0, 0],
            [30.0, 0, 0],
        ], dtype=np.float64)
        m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=0, property_id=0)
        # Element uses nodes 200, 300 (indices 1,2 in the array)
        m.mesh.add(FCElement({
            'id': 50, 'type': 'SPRING3D', 'nodes': [200, 300],
            'parent_id': 0, 'block': 1, 'order': 1,
        }))
        m.compress()
        elem = list(m.mesh)[0]
        # 200 -> 2, 300 -> 3
        assert elem.nodes == [2, 3]
        # xyz for node 2 = [20,0,0], node 3 = [30,0,0]
        np.testing.assert_array_equal(m.mesh.nodes_xyz[1], [20.0, 0, 0])
        np.testing.assert_array_equal(m.mesh.nodes_xyz[2], [30.0, 0, 0])

    def test_block_material_steps_untouched(self):
        """material['steps'] should NOT be remapped — only material['ids']."""
        m = FCModel()
        mat = m.add_material("M1")  # id=1
        mat2 = FCMaterial(id=5, name="M2")
        m.materials[5] = mat2
        blk = FCBlock(id=3, cs_id=1, material_id=1, property_id=0)
        blk.material = {'ids': [1, 5], 'steps': [10, 20]}
        m.blocks[3] = blk
        m.compress()
        assert m.blocks[1].material is not None
        assert m.blocks[1].material['ids'] == [1, 2]  # 1->1, 5->2
        assert m.blocks[1].material['steps'] == [10, 20]  # unchanged

