from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKEmulatorMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with IK emulators.
    """

    # region Attributes
    envelope = mpyattribute.MPyAttribute('envelope')
    forwardAxis = mpyattribute.MPyAttribute('forwardAxis')
    forwardAxisFlip = mpyattribute.MPyAttribute('forwardAxisFlip')
    upAxis = mpyattribute.MPyAttribute('upAxis')
    upAxisFlip = mpyattribute.MPyAttribute('upAxisFlip')
    restMatrix = mpyattribute.MPyAttribute('restMatrix')
    poleType = mpyattribute.MPyAttribute('poleType')
    poleVector = mpyattribute.MPyAttribute('poleVector')
    poleVectorX = mpyattribute.MPyAttribute('poleVectorX')
    poleVectorY = mpyattribute.MPyAttribute('poleVectorY')
    poleVectorZ = mpyattribute.MPyAttribute('poleVectorZ')
    poleMatrix = mpyattribute.MPyAttribute('poleMatrix')
    twist = mpyattribute.MPyAttribute('twist')
    stretch = mpyattribute.MPyAttribute('stretch')
    soften = mpyattribute.MPyAttribute('soften')
    pin = mpyattribute.MPyAttribute('pin')
    goal = mpyattribute.MPyAttribute('goal')
    segmentScaleCompensate = mpyattribute.MPyAttribute('segmentScaleCompensate')
    parentInverseMatrix = mpyattribute.MPyAttribute('parentInverseMatrix')
    softOrigin = mpyattribute.MPyAttribute('softOrigin')
    softGoal = mpyattribute.MPyAttribute('softGoal')
    softVector = mpyattribute.MPyAttribute('softVector')
    softDistance = mpyattribute.MPyAttribute('softDistance')
    softScale = mpyattribute.MPyAttribute('softScale')
    outMatrix = mpyattribute.MPyAttribute('outMatrix')
    outWorldMatrix = mpyattribute.MPyAttribute('outWorldMatrix')
    # endregion

    # region Dunderscores
    __plugin__ = 'ikEmulator'
    # endregion
