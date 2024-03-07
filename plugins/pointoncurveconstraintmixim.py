import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from ..builtins import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PointOnCurveConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with point-on-curve constraints.
    """

    # region Dunderscores
    __plugin__ = 'pointOnCurveConstraint'

    __targets__ = {
        'targetCurve': 'worldSpace'
    }

    __inputs__ = {
        'constraintRotateOrder': 'rotateOrder',
        'constraintJointOrient': 'jointOrient',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ',
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Attributes
    forwardVector = mpyattribute.MPyAttribute('forwardVector')
    forwardVectorX = mpyattribute.MPyAttribute('forwardVectorX')
    forwardVectorY = mpyattribute.MPyAttribute('forwardVectorY')
    forwardVectorZ = mpyattribute.MPyAttribute('forwardVectorZ')
    upVector = mpyattribute.MPyAttribute('upVector')
    upVectorX = mpyattribute.MPyAttribute('upVectorX')
    upVectorY = mpyattribute.MPyAttribute('upVectorY')
    upVectorZ = mpyattribute.MPyAttribute('upVectorZ')
    worldUpType = mpyattribute.MPyAttribute('worldUpType')
    worldUpVector = mpyattribute.MPyAttribute('worldUpVector')
    worldUpVectorX = mpyattribute.MPyAttribute('worldUpVectorX')
    worldUpVectorY = mpyattribute.MPyAttribute('worldUpVectorY')
    worldUpVectorZ = mpyattribute.MPyAttribute('worldUpVectorZ')
    worldUpMatrix = mpyattribute.MPyAttribute('worldUpMatrix')
    twist = mpyattribute.MPyAttribute('twist')
    offsetTranslate = mpyattribute.MPyAttribute('offsetTranslate')
    offsetTranslateX = mpyattribute.MPyAttribute('offsetTranslateX')
    offsetTranslateY = mpyattribute.MPyAttribute('offsetTranslateY')
    offsetTranslateZ = mpyattribute.MPyAttribute('offsetTranslateZ')
    offsetRotate = mpyattribute.MPyAttribute('offsetRotate')
    offsetRotateX = mpyattribute.MPyAttribute('offsetRotateX')
    offsetRotateY = mpyattribute.MPyAttribute('offsetRotateY')
    offsetRotateZ = mpyattribute.MPyAttribute('offsetRotateZ')
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
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

        # Reset offset
        #
        self.offsetTranslate = [0.0, 0.0, 0.0]
        self.offsetRotate = [0.0, 0.0, 0.0]

        # Update offset
        #
        constraintMatrix = self.getAttr('constraintMatrix')
        restMatrix = self.restMatrix()

        offsetMatrix = restMatrix * constraintMatrix.inverse()
        offsetTranslate, offsetRotate, offsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)

        self.offsetTranslate = offsetTranslate
        self.offsetRotate = list(map(math.degrees, offsetRotate))
    # endregion
