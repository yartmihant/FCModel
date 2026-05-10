"""Tests for FCMesh, FCElement, FCElementType, and element constants."""
import numpy as np
import pytest

from fc_model import (
    FCMesh, FCElement, FCElementType,
    FC_ELEMENT_TYPES_KEYID, FC_ELEMENT_TYPES_KEYNAME,
)


class TestFCMeshConstruction:
    def test_empty(self):
        mesh = FCMesh()
        assert len(mesh) == 0
        assert not mesh
        assert mesh.nodes_ids.shape == (0,)
        assert mesh.nodes_xyz.shape == (0, 3)

    def test_bool_nonempty(self):
        mesh = FCMesh()
        mesh.nodes_ids = np.array([1], dtype=np.int32)
        mesh.nodes_xyz = np.array([[0.0, 0.0, 0.0]], dtype=np.float64)
        elem = FCElement({'id': 1, 'type': 'HEX8', 'nodes': list(range(1, 9)),
                          'parent_id': 0, 'block': 1, 'order': 1})
        mesh.add(elem)
        assert bool(mesh)
        assert len(mesh) == 1


class TestFCMeshElementAccess:
    @pytest.fixture
    def mesh_with_elements(self):
        mesh = FCMesh()
        mesh.nodes_ids = np.arange(1, 9, dtype=np.int32)
        mesh.nodes_xyz = np.zeros((8, 3), dtype=np.float64)
        e1 = FCElement({'id': 1, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                        'parent_id': 0, 'block': 1, 'order': 1})
        e2 = FCElement({'id': 2, 'type': 'HEX8', 'nodes': [1, 2, 3, 4, 5, 6, 7, 8],
                        'parent_id': 0, 'block': 1, 'order': 1})
        mesh.add(e1)
        mesh.add(e2)
        return mesh

    def test_len(self, mesh_with_elements):
        assert len(mesh_with_elements) == 2

    def test_iter(self, mesh_with_elements):
        ids = [e.id for e in mesh_with_elements]
        assert set(ids) == {1, 2}

    def test_contains_by_id(self, mesh_with_elements):
        assert 1 in mesh_with_elements
        assert 999 not in mesh_with_elements

    def test_getitem_by_id(self, mesh_with_elements):
        elem = mesh_with_elements[1]
        assert isinstance(elem, FCElement)
        assert elem.id == 1

    def test_getitem_by_type(self, mesh_with_elements):
        tetra_dict = mesh_with_elements['TETRA4']
        assert isinstance(tetra_dict, dict)
        assert 1 in tetra_dict

    def test_getitem_missing_raises(self, mesh_with_elements):
        with pytest.raises(KeyError):
            mesh_with_elements[999]

    def test_setitem(self, mesh_with_elements):
        e3 = FCElement({'id': 3, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                        'parent_id': 0, 'block': 1, 'order': 1})
        mesh_with_elements[3] = e3
        assert 3 in mesh_with_elements

    def test_add_auto_id(self, mesh_with_elements):
        """add() auto-assigns ID if id < 1 or collides."""
        e = FCElement({'id': 0, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                       'parent_id': 0, 'block': 1, 'order': 1})
        assigned_id = mesh_with_elements.add(e)
        assert assigned_id > 2  # bigger than existing max

    def test_max_id(self, mesh_with_elements):
        assert mesh_with_elements.max_id == 2

    def test_nodes_list(self, mesh_with_elements):
        nl = mesh_with_elements.nodes_list
        assert isinstance(nl, list)
        assert len(nl) == 4 + 8  # TETRA4 has 4 nodes, HEX8 has 8


class TestFCMeshCompress:
    def test_compress_reindexes(self):
        mesh = FCMesh()
        mesh.nodes_ids = np.arange(1, 5, dtype=np.int32)
        mesh.nodes_xyz = np.zeros((4, 3), dtype=np.float64)
        e1 = FCElement({'id': 10, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                        'parent_id': 0, 'block': 1, 'order': 1})
        e2 = FCElement({'id': 20, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                        'parent_id': 0, 'block': 1, 'order': 1})
        mesh.add(e1)
        mesh.add(e2)

        index_map = mesh.compress()
        assert 10 in index_map
        assert 20 in index_map
        ids = sorted(e.id for e in mesh)
        assert ids == [1, 2]


class TestFCMeshEncodeDecode:
    def test_roundtrip(self):
        mesh = FCMesh()
        mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
        mesh.nodes_xyz = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)
        e = FCElement({'id': 1, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
                       'parent_id': 0, 'block': 1, 'order': 1})
        mesh.add(e)

        encoded = mesh.encode()
        assert encoded['nodes_count'] == 4
        assert encoded['elems_count'] == 1

        mesh2 = FCMesh()
        mesh2.decode(encoded)
        assert len(mesh2) == 1
        np.testing.assert_array_equal(mesh2.nodes_ids, mesh.nodes_ids)
        np.testing.assert_array_almost_equal(mesh2.nodes_xyz, mesh.nodes_xyz)

        elem = next(iter(mesh2))
        assert elem.id == 1
        assert elem.type == 'TETRA4'
        assert elem.nodes == [1, 2, 3, 4]

    def test_decode_nodes_count_mismatch_raises(self):
        mesh = FCMesh()
        mesh.nodes_ids = np.array([1, 2], dtype=np.int32)
        mesh.nodes_xyz = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        encoded = mesh.encode()
        encoded['nodes_count'] = 999  # wrong
        mesh2 = FCMesh()
        with pytest.raises(ValueError, match="nodes_count"):
            mesh2.decode(encoded)


class TestElementConstants:
    def test_keyid_keyname_consistent(self):
        """Every entry in KEYID should have a matching entry in KEYNAME."""
        for fc_id, info in FC_ELEMENT_TYPES_KEYID.items():
            name = info['name']
            assert name in FC_ELEMENT_TYPES_KEYNAME
            assert FC_ELEMENT_TYPES_KEYNAME[name]['fc_id'] == fc_id

    def test_keyname_keyid_consistent(self):
        for name, info in FC_ELEMENT_TYPES_KEYNAME.items():
            fc_id = info['fc_id']
            assert fc_id in FC_ELEMENT_TYPES_KEYID
            assert FC_ELEMENT_TYPES_KEYID[fc_id]['name'] == name

    def test_tetra4_properties(self):
        t = FC_ELEMENT_TYPES_KEYNAME['TETRA4']
        assert t['fc_id'] == 1
        assert t['dim'] == 3
        assert t['nodes'] == 4
        assert t['order'] == 1

    def test_hex8_properties(self):
        h = FC_ELEMENT_TYPES_KEYNAME['HEX8']
        assert h['fc_id'] == 3
        assert h['dim'] == 3
        assert h['nodes'] == 8
