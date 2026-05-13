
# from fc_model import FCModel

# def compress(self: FCModel):

#     # TODO всюду где есть ссылки на узлы и элементы, осуществить грамотную переиндексацию
#     # TODO добавить системы координат


#     # 1. Убираем неиспользуемые узлы и переиндексируем используемые

#     nodes_id_map = {index: i + 1
#                     for i, index in enumerate(set(self.elems.nodes_list))}

#     self.nodes.reindex(nodes_id_map)

#     for elem in self.elems:
#         elem['nodes'] = [nodes_id_map[nid] for nid in elem['nodes']]

#     # 2. Убираем неиспользуемые блоки и переиндексируем используемые

#     blocks_id_map = {index: i + 1
#                         for i, index in enumerate(set([elem['block'] for elem in self.elems]))}

#     self.blocks.reindex(blocks_id_map)

#     for elem in self.elems:
#         elem['block'] = blocks_id_map[elem['block']]


#     # 3. Убираем неиспользуемые свойтсва и переиндексируем используемые

#     property_id_map = {index: i + 1
#                         for i, index in enumerate(set([block['property_id']
#                                                         for block in self.blocks]))}

#     self.property_tables.reindex(property_id_map)

#     for block in self.blocks:
#         block['property_id'] = property_id_map[block['property_id']]

#     # 4. Переиндексируем используемые материалы

#     material_id_map = self.materials.compress()

#     for block in self.blocks:
#         block['material_id'] = material_id_map[block['material_id']]


#     # 5. Переиндексируем используемые граничные условия

#     load_id_map = self.loads.compress()

#     restraint_id_map = self.restraints.compress()


#     # 6. Переиндексируем существующие элементы

#     elems_id_map = self.elems.compress()

#     for material in self.materials:
#         for key in material['properties']:
#             for property in material['properties'][key]:

#                 if isinstance(property['dependency'], list) and property['dependency']:
#                     for dep in property['dependency']:
#                         if isinstance(dep['data'], ndarray):
#                             if dep['type'] == 10:
#                                 for i, n in enumerate(dep['data']):
#                                     dep['data'][i] = elems_id_map[int(n)]
#                             if dep['type'] == 11:
#                                 for i, n in enumerate(dep['data']):
#                                     dep['data'][i] = nodes_id_map[int(n)]






# def split_face(face: List[int]) -> List[int]:
#     if len(face) == 3:
#         return face
#     if len(face) < 3:
#         return []
#     tail = face[2:]
#     tail.append(face[1])
#     tris = [face[-1], face[0], face[1]]
#     tris.extend(split_face(tail))
#     return tris


# def split_edge(edge: List[int]) -> List[int]:
#     if len(edge) == 2:
#         return edge
#     if len(edge) < 2:
#         return []
#     tail = edge[1:]
#     pairs = [edge[0], edge[1]]
#     pairs.extend(split_edge(tail))
#     return pairs


# def make_structure():
#     for eid in FC_ELEMENT_TYPES:
#         element_type = FC_ELEMENT_TYPES[eid]
#         element_type['structure'][0] = np.arange(element_type['nodes_count'], dtype=np.int32)

#         if element_type['dim'] > 0:

#             pairs = []
#             for edge in element_type['edges']:
#                 pairs.extend(split_edge(edge))

#             element_type['structure'][1] = np.array(pairs, dtype=np.int32)

#         if element_type['dim'] > 1:

#             trangles = []
#             for face in element_type['faces']:
#                 trangles.extend(split_face(face))

#             element_type['structure'][2] = np.array(trangles, dtype=np.int32)
