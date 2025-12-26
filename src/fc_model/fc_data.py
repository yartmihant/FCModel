from __future__ import annotations
# Dependency (const_types) enumeration mapping
from typing import Dict, List, Literal, Optional, Sequence, Tuple, Union

import numpy as np
from numpy import dtype, float64, generic
from numpy.typing import NDArray

from .fc_value import FCValue

# Dependency types (FCData)
FC_DEPENDENCY_TYPES_KEYS: Dict[int, str] = {
    0: "CONSTANT",
    1: "TABULAR_X",
    2: "TABULAR_Y",
    3: "TABULAR_Z",
    4: "TABULAR_TIME",
    5: "TABULAR_TEMPERATURE",
    6: "FORMULA",
    7: "TABULAR_FREQUENCY",
    8: "TABULAR_STRAIN",
    10: "TABULAR_ELEMENT_ID",
    11: "TABULAR_NODE_ID",
    12: "TABULAR_MODE_ID",
}

FC_DEPENDENCY_TYPES_CODES: Dict[str, int] = {v: k for k, v in FC_DEPENDENCY_TYPES_KEYS.items()}


class FCDependencyColumn:
    type: str  # Форма задания зависимости - значение из DEPENDENCY_TYPES
    value: FCValue

    def __init__(self, type: str, value: FCValue):
        self.type = type
        self.value = value

    def __str__(self) -> str:
        return f"FCDependencyColumn(type={self.type}, value={self.value})"

    def __repr__(self) -> str:
        return f"<FCDependencyColumn type={self.type!r}>"


class FCData:
    """
    Определяет зависимость свойства от внешних факторов (температура, координаты, etc.).
    """
    type: Union[int, str] # -1 - таблица, иное число - константа

    value: FCValue  # Данные для зависимости (e.g., массив ID узлов)
    table: List[FCDependencyColumn]

    def __init__(self, value: FCValue, type_code: Union[int, str] = 0, table: Optional[List[FCDependencyColumn]] = None):
        self.value = value
        self.type = type_code
        self.table = table if table is not None else []

    @classmethod
    def constant(cls, values: Union[float, int, Sequence[Union[float, int]]]) -> FCData:
        """
        Удобный конструктор константного значения (type=0) в формате float64 массива.
        """
        if isinstance(values, (list, tuple, np.ndarray)):
            arr = np.asarray(values, dtype=float64)
        else:
            arr = np.asarray([values], dtype=float64)
        return cls(FCValue(arr, 'array'), 0, [])

    @classmethod
    def formula(cls, expr: str) -> FCData:
        """
        Удобный конструктор формулы (type=6).
        """
        return cls(FCValue(expr, 'formula'), 6, [])

    @classmethod
    def decode(cls, data: Union[NDArray[generic], str], dep_type: Union[List[int], int, str], dep_data: Union[List[NDArray[generic]], List[str], str, None]) -> FCData:
        
        if isinstance(dep_type, list) and isinstance(dep_data, list):
            
            value = FCValue.decode(data, dtype(float64))
            
            if len(dep_type) != len(dep_data):
                raise ValueError("FCData: dep_type and dep_data lists must have equal lengths")
            
            table = [FCDependencyColumn(
                type = FC_DEPENDENCY_TYPES_KEYS[deps_type],
                value = FCValue.decode(dep_data[j], dtype(float64))
            ) for j, deps_type in enumerate(dep_type)]
            
            return cls(value, -1, table)

        elif (isinstance(dep_type, int) or isinstance(dep_type, str)) and isinstance(dep_data, str):
            val_type:Literal['formula', 'array', 'null'] = 'formula' if dep_type == 6 else 'array'
            value = FCValue.decode(data, dtype(float64), val_type)
            return cls(value, dep_type, [])
        else:
             raise ValueError("Invalid dependency data for decode")

    def encode(self) -> Union[Tuple[str, List[int], List[str]], Tuple[str, Union[int, str], str]]:
        if self.type == -1:
            return self.value.encode(), [FC_DEPENDENCY_TYPES_CODES[deps.type] for deps in self.table], [deps.value.encode() for deps in self.table]
        else:
            return self.value.encode(), self.type, ""


    def __len__(self) -> int:
        if not len(self.table):
            return 0
        return len(self.table[0].value)

    def __str__(self) -> str:
        return (
            f"FCData(type={self.type}, value={self.value}, table={self.table})"
        )

    def __repr__(self) -> str:
        if self.type == -1:
            return f"<FCData TABLE [{len(self)}])>"
        elif self.type == 6:
            return f"<FCData FORMULA {self.value.data}>"
        elif self.type == 0:
            return f"<FCData CONST {self.value.data}>"
        else:
            return f"<FCData <{self.type}>>"
