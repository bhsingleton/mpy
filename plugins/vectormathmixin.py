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
    Enum class of all available operations.
    """

    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    ABSOLUTE = 4
    NEGATE = 5
    HALF = 6
    MIN = 7
    MAX = 8
    AVERAGE = 9
    POW = 10
    ROOT = 11
    NORMALIZE = 12
    LENGTH = 13
    DISTANCE = 14
    ANGLE = 15
    DOT = 16
    CROSS = 17
    PROJECT = 18
    LERP = 19


class VectorMathMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with vector-math nodes.
    """

    # region Dunderscores
    __plugin__ = 'vectorMath'
    # endregion

    # region Enums
    Operation = Operation
    # endregion

    # region Attributes
    operation = mpyattribute.MPyAttribute('operation')
    normalize = mpyattribute.MPyAttribute('normalize')
    weight = mpyattribute.MPyAttribute('weight')
    inFloatA = mpyattribute.MPyAttribute('inFloatA')
    inFloatB = mpyattribute.MPyAttribute('inFloatB')
    inDistanceA = mpyattribute.MPyAttribute('inDistanceA')
    inDistanceB = mpyattribute.MPyAttribute('inDistanceB')
    inAngleA = mpyattribute.MPyAttribute('inAngleA')
    inAngleB = mpyattribute.MPyAttribute('inAngleB')
    outFloat = mpyattribute.MPyAttribute('outFloat')
    outDistance = mpyattribute.MPyAttribute('outDistance')
    outAngle = mpyattribute.MPyAttribute('outAngle')
    # endregion
