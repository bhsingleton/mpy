from maya.api import OpenMaya as om
from enum import IntEnum
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AimMatrixMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with aim matrix nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kAimMatrix
    # endregion

    # region Attributes
    enable = mpyattribute.MPyAttribute('enable')
    envelope = mpyattribute.MPyAttribute('envelope')
    inputMatrix = mpyattribute.MPyAttribute('inputMatrix')
    primary = mpyattribute.MPyAttribute('primary')
    primaryInputAxis = mpyattribute.MPyAttribute('primaryInputAxis')
    primaryInputAxisX = mpyattribute.MPyAttribute('primaryInputAxisX')
    primaryInputAxisY = mpyattribute.MPyAttribute('primaryInputAxisY')
    primaryInputAxisZ = mpyattribute.MPyAttribute('primaryInputAxisZ')
    primaryMode = mpyattribute.MPyAttribute('primaryMode')
    primaryTargetVector = mpyattribute.MPyAttribute('primaryTargetVector')
    primaryTargetVectorX = mpyattribute.MPyAttribute('primaryTargetVectorX')
    primaryTargetVectorY = mpyattribute.MPyAttribute('primaryTargetVectorY')
    primaryTargetVectorZ = mpyattribute.MPyAttribute('primaryTargetVectorZ')
    primaryTargetMatrix = mpyattribute.MPyAttribute('primaryTargetMatrix')
    secondary = mpyattribute.MPyAttribute('secondary')
    secondaryInputAxis = mpyattribute.MPyAttribute('secondaryInputAxis')
    secondaryInputAxisX = mpyattribute.MPyAttribute('secondaryInputAxisX')
    secondaryInputAxisY = mpyattribute.MPyAttribute('secondaryInputAxisY')
    secondaryInputAxisZ = mpyattribute.MPyAttribute('secondaryInputAxisZ')
    secondaryMode = mpyattribute.MPyAttribute('secondaryMode')
    secondaryTargetVector = mpyattribute.MPyAttribute('secondaryTargetVector')
    secondaryTargetVectorX = mpyattribute.MPyAttribute('secondaryTargetVectorX')
    secondaryTargetVectorY = mpyattribute.MPyAttribute('secondaryTargetVectorY')
    secondaryTargetVectorZ = mpyattribute.MPyAttribute('secondaryTargetVectorZ')
    outputMatrix = mpyattribute.MPyAttribute('outputMatrix')
    # endregion
