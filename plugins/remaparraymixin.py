from maya.api import OpenMaya as om
from enum import IntEnum
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Function(IntEnum):
    """
    Enum class of all available remap functions.
    """

    CUSTOM = 0
    EASE_IN = 1
    EASE_OUT = 2
    EASE_BOTH = 3


class RemapArrayMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with remap-array nodes.
    """

    # region Enums
    Function = Function
    # endregion

    # region Dunderscores
    __plugin__ = 'remapArray'
    # endregion

    # region Attributes
    function = mpyattribute.MPyAttribute('function')
    coefficient = mpyattribute.MPyAttribute('coefficient')
    parameter = mpyattribute.MPyAttribute('parameter')
    value = mpyattribute.MPyAttribute('value')
    color = mpyattribute.MPyAttribute('color')
    clamp = mpyattribute.MPyAttribute('clamp')
    inputMin = mpyattribute.MPyAttribute('inputMin')
    inputMax = mpyattribute.MPyAttribute('inputMax')
    outputMin = mpyattribute.MPyAttribute('outputMin')
    outputMax = mpyattribute.MPyAttribute('outputMax')
    outValue = mpyattribute.MPyAttribute('outValue')
    outColor = mpyattribute.MPyAttribute('outColor')
    # endregion
