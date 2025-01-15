from maya.api import OpenMaya as om
from enum import IntEnum
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CurveFromPointMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with curve-from-point nodes.
    """

    # region Dunderscores
    __plugin__ = 'curveFromPoint'
    # endregion

    # region Attributes
    degree = mpyattribute.MPyAttribute('degree')
    rational = mpyattribute.MPyAttribute('rational')
    planar = mpyattribute.MPyAttribute('planar')
    inputPoint = mpyattribute.MPyAttribute('inputPoint')
    inputMatrix = mpyattribute.MPyAttribute('inputMatrix')
    parentInverseMatrix = mpyattribute.MPyAttribute('parentInverseMatrix')
    outCurve = mpyattribute.MPyAttribute('outCurve')
    # endregion
