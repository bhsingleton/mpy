import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..nodetypes import constraintmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class OrientationConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with orientation constraints.
    """

    # region Dunderscores
    __plugin__ = 'orientationConstraint'

    __targets__ = {
        'targetMatrix': 'matrix',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintRotateOrder': 'rotateOrder',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Attributes
    localOrWorld = mpyattribute.MPyAttribute('localOrWorld')
    relative = mpyattribute.MPyAttribute('relative')
    offsetRotate = mpyattribute.MPyAttribute('offsetRotate')
    offsetRotateX = mpyattribute.MPyAttribute('offsetRotateX')
    offsetRotateY = mpyattribute.MPyAttribute('offsetRotateY')
    offsetRotateZ = mpyattribute.MPyAttribute('offsetRotateZ')
    restRotate = mpyattribute.MPyAttribute('restRotate')
    restRotateX = mpyattribute.MPyAttribute('restRotateX')
    restRotateY = mpyattribute.MPyAttribute('restRotateY')
    restRotateZ = mpyattribute.MPyAttribute('restRotateZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        # Temporarily disable offset
        #
        self.relative = False

        # Calculate offset
        #
        constraintMatrix = self.getAttr('constraintMatrix')
        restMatrix = self.restMatrix()

        offsetMatrix = restMatrix * constraintMatrix.inverse()
        offsetEulerRotation = transformutils.decomposeTransformMatrix(offsetMatrix)[1]

        # Update and re-enable offset
        #
        self.offsetRotateX = math.degrees(offsetEulerRotation.x)
        self.offsetRotateY = math.degrees(offsetEulerRotation.y)
        self.offsetRotateZ = math.degrees(offsetEulerRotation.z)
        self.relative = True
    # endregion
