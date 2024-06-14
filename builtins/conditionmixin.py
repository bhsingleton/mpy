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

    EQUAL = 0
    NOT_EQUAL = 1
    GREATER_THAN = 2
    GREAT_OR_EQUAL = 3
    LESS_THAN = 4
    LESS_OR_EQUAL = 5


class ConditionMixin(dependencymixin.DependencyMixin):
    """
    Overload of `ConditionMixin` that interfaces with condition nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kCondition
    # endregion

    # region Enums
    Operation = Operation
    # endregion

    # region Attributes
    firstTerm = mpyattribute.MPyAttribute('firstTerm')
    secondTerm = mpyattribute.MPyAttribute('secondTerm')
    operation = mpyattribute.MPyAttribute('operation')
    colorIfTrue = mpyattribute.MPyAttribute('colorIfTrue')
    colorIfTrueR = mpyattribute.MPyAttribute('colorIfTrueR')
    colorIfTrueG = mpyattribute.MPyAttribute('colorIfTrueG')
    colorIfTrueB = mpyattribute.MPyAttribute('colorIfTrueB')
    colorIfFalse = mpyattribute.MPyAttribute('colorIfFalse')
    colorIfFalseR = mpyattribute.MPyAttribute('colorIfFalseR')
    colorIfFalseG = mpyattribute.MPyAttribute('colorIfFalseG')
    colorIfFalseB = mpyattribute.MPyAttribute('colorIfFalseB')
    # endregion
