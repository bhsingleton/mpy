from maya.api import OpenMaya as om
from enum import IntEnum
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Operation(IntEnum):
    """
    Enum class of condition operations.
    """

    NO_OPERATION = 0
    DOT_PRODUCT = 1
    CROSS_PRODUCT = 2
    VECTOR_MATRIX_PRODUCT = 3
    POINT_MATRIX_PRODUCT = 4


class VectorProductMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with vector-product nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kVectorProduct
    # endregion

    # region Enums
    Operation = Operation
    # endregion

    # region Attributes
    operation = mpyattribute.MPyAttribute('operation')
    normalizeOutput = mpyattribute.MPyAttribute('normalizeOutput')
    input1 = mpyattribute.MPyAttribute('input1')
    input1X = mpyattribute.MPyAttribute('input1X')
    input1Y = mpyattribute.MPyAttribute('input1Y')
    input1Z = mpyattribute.MPyAttribute('input1Z')
    input2 = mpyattribute.MPyAttribute('input2')
    input2X = mpyattribute.MPyAttribute('input2X')
    input2Y = mpyattribute.MPyAttribute('input2Y')
    input2Z = mpyattribute.MPyAttribute('input2Z')
    output = mpyattribute.MPyAttribute('output')
    outputX = mpyattribute.MPyAttribute('outputX')
    outputY = mpyattribute.MPyAttribute('outputY')
    outputZ = mpyattribute.MPyAttribute('outputZ')
    # endregion
