from __future__ import annotations
import json

from typing import Any, Sequence, TypedDict, Optional, Dict, List, Union

import numpy as np
from numpy import int32
from numpy.typing import NDArray

from .fc_blocks import FCBlock, FCSrcBlock
from .fc_conditions import FC_INITIAL_SET_TYPES_CODES, FC_INITIAL_SET_TYPES_KEYS, \
    FC_LOADS_TYPES_CODES, FC_LOADS_TYPES_KEYS, FC_RESTRAINT_FLAGS_CODES, FC_RESTRAINT_FLAGS_KEYS, FCInitialSet, FCRestraint, FCLoad, FCSrcInitialSet, FCSrcLoad, FCSrcRestraint
from .fc_constraint import FCConstraint, FCSrcConstraint
from .fc_coordinate_system import FCCoordinateSystem, FCSrcCoordinateSystem
from .fc_data import FC_DEPENDENCY_TYPES_CODES, FC_DEPENDENCY_TYPES_KEYS, FCData, FCDependencyColumn
from .fc_materials import FC_MATERIAL_PROPERTY_NAMES_CODES, FC_MATERIAL_PROPERTY_NAMES_KEYS, FC_MATERIAL_PROPERTY_TYPES_CODES, FC_MATERIAL_PROPERTY_TYPES_KEYS, FCMaterial, FCMaterialPropertiesTypeLiteral, FCMaterialProperty, FCSrcMaterial
from .fc_mesh import FCMesh, FCSrcMesh
from .fc_elements import FC_ELEMENT_TYPES_KEYID, FC_ELEMENT_TYPES_KEYNAME, FCElement, FCElementType
from .fc_property_tables import FCPropertyTable, FCSrcPropertyTable
from .fc_receivers import FCReceiver, FCSrcReceiver
from .fc_set import FCSet, FCSrcSet
from .fc_value import FCValue


class FCHeader(TypedDict):
    binary: bool
    description: str
    version: int
    types: dict[str, int]


class FCSettings(TypedDict, total=False):
    type: str  # Тип расчета ("static", "dynamic", "eigenfrequencies", "buckling", "spectrum", "harmonic", "effectiveprops")
    dimensions: str  # Размерность задачи ("2D", "3D")
    plane_state: str  # Вид расчетов для "2D" ("p-stress", "p-strain", "axisym_x", "axisym_y")
    permission_write: bool  # Разрешить запись на диск при нехватке ОЗУ
    periodic_bc: bool  # Периодические ГУ для расчета эффективных свойств
    finite_deformations: bool  # Включить конечные деформации
    elasticity: bool  # Включить упругость
    plasticity: bool  # Включить пластичность
    heat_transfer: bool  # Включить теплопроводность
    porefluid_transfer: bool  # Включить пьезопроводность
    slm: bool  # Включить аддитивное производство
    incompressibility: bool  # Включить несжимаемость
    preload: bool  # Преднагруженная модель
    lumpmass: bool  # Использовать лумпингованую диагональную матрицу масс
    radiation_among_surfaces: bool  # Включить лучистый теплообмен
    linear_solver: Dict[str, Any]  # Настройки линейного решателя
    nonlinear_solver: Dict[str, Any]  # Настройки нелинейного решателя
    damping: Dict[str, Any]  # Настройки демпфирования
    thermal_gap_settings: Dict[str, Any]  # Настройки решателя для газового зазора
    eigen_solver: Dict[str, Any]  # Настройки решателя собственных частот
    dynamics: Dict[str, Any]  # Настройки динамического расчета
    statics: Dict[str, Any]  # Настройки статического расчета
    harmonic: Dict[str, Any]  # Настройки гармонического расчета
    output: Dict[str, Any]  # Настройки вывода данных
    test_opts: Dict[str, Any]  # Настройки отладочной версии ядра


class FCSrcModelStrict(TypedDict):
    header: FCHeader
    settings: FCSettings
    mesh: FCSrcMesh


class FCSrcModel(FCSrcModelStrict, total=False):

    coordinate_systems: List[FCSrcCoordinateSystem]
    blocks: List[FCSrcBlock]

    property_tables: List[FCSrcPropertyTable]
    materials: List[FCSrcMaterial]

    loads: List[FCSrcLoad]
    restraints: List[FCSrcRestraint]
    initial_sets: List[FCSrcInitialSet]

    contact_constraints: List[FCSrcConstraint]
    coupling_constraints: List[FCSrcConstraint]
    periodic_constraints: List[FCSrcConstraint]

    receivers: List[FCSrcReceiver]

    sets: Dict[str, List[FCSrcSet]]



class FCModel:
    """
    Основной класс для представления, загрузки и сохранения модели в формате Fidesys Case (.fc).

    Представляет собой контейнер для всех сущностей модели: узлов, элементов,
    материалов, нагрузок, закреплений и т.д.

    Атрибуты:
        header (FCHeader): Заголовок файла.
        coordinate_systems (Dict[int, FCCoordinateSystem]): Коллекция систем координат.
        elems (FCMesh): Контейнер сетки и элементов.
        blocks (Dict[int, FCBlock]): Коллекция блоков, связывающих элементы с материалами.
        materials (Dict[int, FCMaterial]): Коллекция материалов и их физических свойств.
        loads (List[FCLoad]): Список нагрузок, приложенных к модели.
        restraints (List[FCRestraint]): Список закреплений (ограничений).
        ... и другие коллекции сущностей.

    Пример использования:
    
    # Создание или загрузка модели
    model = FCModel() # Создать пустую модель
    # model = FCModel(filepath="path/to/model.fc") # Загрузить из файла

    # ... (добавление узлов, элементов, материалов)

    # Сохранение модели
    model.save("new_model.fc")
    """

    header: FCHeader

    coordinate_systems: Dict[int, FCCoordinateSystem]

    mesh: FCMesh

    blocks: Dict[int, FCBlock]
    property_tables: Dict[int, FCPropertyTable]
    materials: Dict[int, FCMaterial]

    loads: List[FCLoad]
    restraints: List[FCRestraint]
    initial_sets: List[FCInitialSet]

    contact_constraints: List[FCConstraint]
    coupling_constraints: List[FCConstraint]
    periodic_constraints: List[FCConstraint]

    receivers: List[FCReceiver]

    nodesets: Dict[int, FCSet]
    sidesets: Dict[int, FCSet]

    settings: FCSettings

    def __init__(self) -> None:
        """
        Инициализирует объект FCModel.
        """
        
        # Инициализация всех коллекций как пустых
        self.coordinate_systems = {}
        
        self.mesh = FCMesh()

        self.blocks = {}
        self.property_tables = {}
        self.materials = {}
        
        self.loads: List[FCLoad] = []
        self.restraints: List[FCRestraint] = []
        self.initial_sets: List[FCInitialSet] = []

        self.contact_constraints: List[FCConstraint] = []
        self.coupling_constraints: List[FCConstraint] = []
        self.periodic_constraints: List[FCConstraint] = []
        self.receivers: List[FCReceiver] = []

        self.nodesets = {}
        self.sidesets = {}

        self.settings = {}
        self.header = {
            "binary": True,
            "description": "Fidesys Case Format",
            "types": {"char": 1, "short_int": 2, "int": 4, "double": 8, },
            "version": 3
        }

        self.add_coordinate_system('base')


    def add_coordinate_system(self, name: str, type_name: str = "cartesian") -> FCCoordinateSystem:
        """
        Создает и добавляет новую систему координат в модель.
        Автоматически назначает уникальный ID.
        """
        new_id = max(self.coordinate_systems.keys(), default=0) + 1
        coordinate_system = FCCoordinateSystem(id=new_id, name=name, type_name=type_name)
        self.coordinate_systems[new_id] = coordinate_system
        return coordinate_system

    def add_material(self, name: str) -> FCMaterial:
        """
        Создает и добавляет новый материал в модель, автоматически назначая уникальный ID.
        """
        new_id = max(self.materials.keys(), default=0) + 1
        material = FCMaterial(id=new_id, name=name)
        self.materials[new_id] = material
        return material

    def add_material_property(
        self,
        material_id: int,
        group_name: FCMaterialPropertiesTypeLiteral,
        property_name: str,
        values: Union[str, float, int, Sequence[Union[float, int]]],
        property_type: Optional[str] = None,
    ) -> FCMaterialProperty:
        """
        Удобный хелпер: добавляет свойство материалу по id через FCMaterial.add_property().
        """
        mat = self.materials[material_id]
        if isinstance(values, str):
            v: Union[str, float, int, List[Union[str, float, int]]] = values
        elif isinstance(values, (float, int)):
            v = values
        else:
            v = list(values)
        return mat.add_property(
            group_name=group_name, property_name=property_name, values=v, property_type=property_type
        )

    def _make_apply_value(self, apply_to: Union[str, Sequence[int], NDArray[Any]]) -> FCValue:
        """
        Внутренний хелпер: формирует FCValue для apply_to.
        - строка (например 'all') хранится как формула
        - последовательность id -> int32 массив
        """
        if isinstance(apply_to, str):
            return FCValue.decode(apply_to, np.dtype('int32'))
        arr = np.asarray(list(apply_to), dtype=int32)
        return FCValue(arr, 'array')

    def add_load(
        self,
        name: str,
        type: str,
        apply_to: Union[str, Sequence[int], NDArray[Any]],
        *,
        cs_id: int = 0,
        data: Optional[List[FCData]] = None,
    ) -> FCLoad:
        """
        Создает и добавляет нагрузку в модель.
        """
        new_id = max((l.id for l in self.loads), default=0) + 1
        load = FCLoad(id=new_id)
        load.name = name
        load.type = type
        load.cs_id = cs_id
        load.apply = self._make_apply_value(apply_to)
        load.data = data if data is not None else []
        self.loads.append(load)
        return load

    def add_restraint(
        self,
        name: str,
        flags: List[str],
        apply_to: Union[str, Sequence[int], NDArray[Any]],
        *,
        cs_id: int = 0,
        data: Optional[List[FCData]] = None,
    ) -> FCRestraint:
        """
        Создает и добавляет закрепление (ГУ) в модель.
        """
        new_id = max((r.id for r in self.restraints), default=0) + 1
        rest = FCRestraint(id=new_id)
        rest.name = name
        rest.flags = flags
        rest.cs_id = cs_id
        rest.apply = self._make_apply_value(apply_to)
        rest.data = data if data is not None else []
        self.restraints.append(rest)
        return rest

    def add_initial_set(
        self,
        type: str,
        apply_to: Union[str, Sequence[int], NDArray[Any]],
        *,
        flags: Optional[List[str]] = None,
        cs_id: int = 0,
        data: Optional[List[FCData]] = None,
    ) -> FCInitialSet:
        """
        Создает и добавляет начальные условия (Initial Set) в модель.
        """
        new_id = max((s.id for s in self.initial_sets), default=0) + 1
        init = FCInitialSet(id=new_id)
        init.type = type
        init.flags = flags if flags is not None else []
        init.cs_id = cs_id
        init.apply = self._make_apply_value(apply_to)
        init.data = data if data is not None else []
        self.initial_sets.append(init)
        return init

    def add_nodeset(self, name: str, apply_to: Sequence[int]) -> FCSet:
        """
        Создает и добавляет nodeset в модель.
        """
        new_id = max(self.nodesets.keys(), default=0) + 1
        s = FCSet(id=new_id, name=name)
        s.apply = self._make_apply_value(apply_to)
        self.nodesets[new_id] = s
        return s

    def add_sideset(self, name: str, apply_to: Sequence[int]) -> FCSet:
        """
        Создает и добавляет sideset в модель.
        """
        new_id = max(self.sidesets.keys(), default=0) + 1
        s = FCSet(id=new_id, name=name)
        s.apply = self._make_apply_value(apply_to)
        self.sidesets[new_id] = s
        return s


    @classmethod
    def load(cls, filepath: str) -> FCModel:
        """
        Сохраняет текущее состояние модели в файл формата .fc.
        """

        with open(filepath, "r") as f:
            src_data = json.load(f)
            return FCModel.decode(src_data)


    def save(self, filepath: str) -> None:
        """
        Сохраняет текущее состояние модели в файл формата .fc.
        """
        with open(filepath, "w") as f:
            json.dump(self.encode(), f, indent=4)


    @classmethod
    def decode(cls, src_data: FCSrcModel) -> FCModel:

        fc_model = FCModel()

        header_data: FCHeader = src_data['header']
        if header_data is not None:
            fc_model.header = header_data

        fc_model.coordinate_systems = {}
        for src in src_data.get('coordinate_systems', []):
            cs = FCCoordinateSystem.decode(src)
            fc_model.coordinate_systems[cs.id] = cs

        fc_model.materials = {}
        for src_material in src_data.get('materials', []):
            material = FCMaterial.decode(src_material)
            fc_model.materials[material.id] = material

        fc_model.blocks = {}
        for src_block in src_data.get('blocks', []):
            blk = FCBlock.decode(src_block)
            fc_model.blocks[blk.id] = blk

        fc_model.mesh.decode(src_data['mesh'])

        fc_model.contact_constraints = [FCConstraint.decode(cc_src) for cc_src in src_data.get('contact_constraints', [])]
        
        fc_model.coupling_constraints = [FCConstraint.decode(cc_src) for cc_src in src_data.get('coupling_constraints', [])]

        fc_model.periodic_constraints = [FCConstraint.decode(cc_src) for cc_src in src_data.get('periodic_constraints', [])]

        fc_model.restraints = [FCRestraint.decode(src_restraint) for src_restraint in src_data.get('restraints', [])]

        fc_model.initial_sets = [FCInitialSet.decode(src_initial_set) for src_initial_set in src_data.get('initial_sets', [])]

        fc_model.loads = [FCLoad.decode(src_load) for src_load in src_data.get('loads', [])]

        fc_model.receivers = [FCReceiver.decode(src_receiver) for src_receiver in src_data.get('receivers', [])]

        fc_model.property_tables = {}
        for pt_src in src_data.get('property_tables', []):
            pt = FCPropertyTable.decode(pt_src)
            fc_model.property_tables[pt.id] = pt

        if 'sets' in src_data:

            fc_model.nodesets = {}
            for ns_src in src_data['sets'].get('nodesets', []):
                ns = FCSet.decode(ns_src)
                fc_model.nodesets[ns.id] = ns

            fc_model.sidesets = {}
            for ss_src in src_data['sets'].get('sidesets', []):
                ss = FCSet.decode(ss_src)
                fc_model.sidesets[ss.id] = ss

        fc_model.settings = src_data.get('settings', {})

        return fc_model


    def encode(self) -> FCSrcModel:
        """
        Собирает данные из всех коллекций (узлы, элементы, материалы и т.д.),
        кодирует их в нужный формат (JSON с base64 для бинарных данных)
 
        Args:
            filepath (str): Путь к файлу, в который будет сохранена модель.
        """

        output_data: FCSrcModel = {
            'header': self.header,
            'settings': self.settings,
            'mesh': self.mesh.encode()
        }

        if self.blocks:
            output_data['blocks'] = [blk.encode() for blk in self.blocks.values()]

        if self.coordinate_systems:
            output_data['coordinate_systems'] = [cs.encode() for cs in self.coordinate_systems.values()]

        if self.contact_constraints:
            output_data['contact_constraints'] = [cc.encode() for cc in self.contact_constraints]

        if self.coupling_constraints:
            output_data['coupling_constraints'] = [cc.encode() for cc in self.coupling_constraints]

        if self.periodic_constraints:
            output_data['periodic_constraints'] = [cc.encode() for cc in self.periodic_constraints]

        if self.nodesets or self.sidesets:
            output_data['sets'] = {}
            if self.nodesets:
                output_data['sets']['nodesets'] = [ns.encode() for ns in self.nodesets.values()]
            if self.sidesets:
                output_data['sets']['sidesets'] = [ss.encode() for ss in self.sidesets.values()]

        if self.property_tables:
            output_data['property_tables'] = [pt.encode() for pt in self.property_tables.values()]

        if self.materials:
            output_data['materials'] = [mat.encode() for mat in self.materials.values()]

        if self.loads:
            output_data['loads'] = [load.encode() for load in self.loads]

        if self.restraints:
            output_data['restraints'] = [restraint.encode() for restraint in self.restraints]

        if self.initial_sets:
            output_data['initial_sets'] = [initial_set.encode() for initial_set in self.initial_sets]

        if self.receivers:
            output_data['receivers'] = [receiver.encode() for receiver in self.receivers]

        return output_data


__all__ = [
    'FCModel',
    'FCMesh', 'FCBlock', 'FCPropertyTable', 'FCCoordinateSystem', 'FCConstraint',
    'FCElement', 'FCElementType', 'FCMaterial', 'FCLoad', 'FCRestraint', 'FCInitialSet',
    'FCReceiver', 'FCSet', 'FCDependencyColumn', 'FCValue', 'FCData', 'FCHeader',
    'FCMaterialProperty',
    'FC_DEPENDENCY_TYPES_KEYS', 'FC_DEPENDENCY_TYPES_CODES',
    'FC_INITIAL_SET_TYPES_CODES', 'FC_INITIAL_SET_TYPES_KEYS',
    'FC_LOADS_TYPES_CODES', 'FC_LOADS_TYPES_KEYS',
    'FC_MATERIAL_PROPERTY_NAMES_CODES', 'FC_MATERIAL_PROPERTY_NAMES_KEYS',
    'FC_MATERIAL_PROPERTY_TYPES_CODES', 'FC_MATERIAL_PROPERTY_TYPES_KEYS',
    'FC_RESTRAINT_FLAGS_CODES', 'FC_RESTRAINT_FLAGS_KEYS',
    'FC_ELEMENT_TYPES_KEYID', 'FC_ELEMENT_TYPES_KEYNAME',
]
