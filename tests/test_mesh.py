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
        for code, info in FC_ELEMENT_TYPES_KEYID.items():
            name = info['name']
            assert name in FC_ELEMENT_TYPES_KEYNAME
            assert FC_ELEMENT_TYPES_KEYNAME[name]['code'] == code

    def test_keyname_keyid_consistent(self):
        for name, info in FC_ELEMENT_TYPES_KEYNAME.items():
            code = info['code']
            assert code in FC_ELEMENT_TYPES_KEYID
            assert FC_ELEMENT_TYPES_KEYID[code]['name'] == name

    def test_tetra4_properties(self):
        t = FC_ELEMENT_TYPES_KEYNAME['TETRA4']
        assert t['code'] == 1
        assert t['dim'] == 3
        assert t['nodes_count'] == 4
        assert t['order'] == 1
        assert t['nodes_coords'] == [
            [0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        assert t['vertices_count'] == 4
        assert t['faces'] == [[0, 2, 3], [1, 2, 3], [0, 1, 3], [0, 1, 2]]

    def test_hex8_properties(self):
        h = FC_ELEMENT_TYPES_KEYNAME['HEX8']
        assert h['code'] == 3
        assert h['dim'] == 3
        assert h['nodes_count'] == 8

    def test_element_type_schema_has_new_keys_only(self):
        t = FC_ELEMENT_TYPES_KEYNAME['HEX20']
        assert 'code' in t
        assert 'nodes_count' in t
        assert 'nodes_coords' in t
        assert 'vertices_count' in t
        assert 'vertices' not in t
        assert 'faces' in t
        assert 'fc_id' not in t
        assert 'nodes' not in t
        assert 'facets' not in t
        assert 'tetras' not in t

    def test_quad8_geometry(self):
        q = FC_ELEMENT_TYPES_KEYNAME['QUAD8']
        assert q['nodes_coords'] == [
            [-1.0, -1.0],
            [1.0, -1.0],
            [1.0, 1.0],
            [-1.0, 1.0],
            [0.0, -1.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [-1.0, 0.0],
        ]
        assert q['vertices_count'] == 4
        assert q['edges'] == [[0, 1, 4], [1, 2, 5], [2, 3, 6], [0, 3, 7]]
        assert q['faces'] == q['edges']

    def test_hex20_geometry(self):
        h = FC_ELEMENT_TYPES_KEYNAME['HEX20']
        assert h['edges'] == [
            [0, 1, 8], [1, 2, 9], [2, 3, 10], [0, 3, 11],
            [4, 5, 12], [5, 6, 13], [6, 7, 14], [4, 7, 15],
            [0, 4, 16], [1, 5, 17], [2, 6, 18], [3, 7, 19],
        ]
        assert h['faces'][0] == [0, 1, 2, 3, 8, 9, 10, 11]
        assert h['faces'][5] == [4, 5, 6, 7, 12, 13, 14, 15]

    def test_wedge15_and_pyr13_geometry(self):
        w = FC_ELEMENT_TYPES_KEYNAME['WEDGE15']
        assert w['edges'] == [
            [0, 1, 6], [1, 2, 7], [0, 2, 8],
            [3, 4, 9], [4, 5, 10], [3, 5, 11],
            [0, 3, 12], [1, 4, 13], [2, 5, 14],
        ]
        assert w['faces'][1] == [1, 2, 4, 5, 7, 10, 13, 14]

        p = FC_ELEMENT_TYPES_KEYNAME['PYR13']
        assert p['edges'] == [
            [0, 1, 5], [1, 2, 6], [2, 3, 7], [0, 3, 8],
            [0, 4, 9], [1, 4, 10], [2, 4, 11], [3, 4, 12],
        ]
        assert p['faces'][4] == [3, 0, 4, 8, 9, 12]
