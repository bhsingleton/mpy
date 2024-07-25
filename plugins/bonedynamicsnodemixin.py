from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BoneDynamicsNodeMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with bone-dynamic nodes.
    """

    # region Dunderscores
    __plugin__ = 'boneDynamicsNode'
    # endregion

    # region Attributes
    enable = mpyattribute.MPyAttribute('enable')
    time = mpyattribute.MPyAttribute('time')
    resetTime = mpyattribute.MPyAttribute('resetTime')
    fps = mpyattribute.MPyAttribute('fps')
    damping = mpyattribute.MPyAttribute('damping')
    elasticity = mpyattribute.MPyAttribute('elasticity')
    stiffness = mpyattribute.MPyAttribute('stiffness')
    mass = mpyattribute.MPyAttribute('mass')
    gravity = mpyattribute.MPyAttribute('gravity')
    gravityX = mpyattribute.MPyAttribute('gravityX')
    gravityY = mpyattribute.MPyAttribute('gravityY')
    gravityZ = mpyattribute.MPyAttribute('gravityZ')
    gravityMultiply = mpyattribute.MPyAttribute('gravityMultiply')
    enableAngleLimit = mpyattribute.MPyAttribute('enableAngleLimit')
    angleLimit = mpyattribute.MPyAttribute('angleLimit')
    radius = mpyattribute.MPyAttribute('radius')
    iterations = mpyattribute.MPyAttribute('iterations')
    enableGroundCol = mpyattribute.MPyAttribute('enableGroundCol')
    groundHeight = mpyattribute.MPyAttribute('groundHeight')
    # endregion
