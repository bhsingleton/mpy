from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SpaceSwitchMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with space-switch nodes.
    """

    # region Dunderscores
    __plugin__ = 'spaceSwitch'
    # endregion

    # region Attributes
    envelope = mpyattribute.MPyAttribute('envelope')
    positionSpace = mpyattribute.MPyAttribute('positionSpace')
    rotationSpace = mpyattribute.MPyAttribute('rotationSpace')
    scaleSpace = mpyattribute.MPyAttribute('scaleSpace')
    weighted = mpyattribute.MPyAttribute('weighted')
    rotateOrder = mpyattribute.MPyAttribute('rotateOrder')
    restMatrix = mpyattribute.MPyAttribute('restMatrix')
    parentInverseMatrix = mpyattribute.MPyAttribute('parentInverseMatrix')
    # endregion
