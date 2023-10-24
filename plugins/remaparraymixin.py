from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RemapArrayMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with remap-array nodes.
    """

    # region Dunderscores
    __plugin__ = 'remapArray'
    # endregion

    # region Attributes
    inValue = mpyattribute.MPyAttribute('inValue')
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
