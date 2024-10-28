import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from enum import IntEnum
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InterpType(IntEnum):
    """
    Enum class of available interpolation types.
    """

    NO_FLIP = 0
    AVERAGE = 1
    SHORTEST = 2
    LONGEST = 3
    CACHE = 4


class OrientConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with orient constraints.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kOrientConstraint

    __targets__ = {
        'targetRotateX': 'rotateX',
        'targetRotateY': 'rotateY',
        'targetRotateZ': 'rotateZ',
        'targetRotateOrder': 'rotateOrder',
        'targetJointOrientX': 'jointOrientX',
        'targetJointOrientY': 'jointOrientY',
        'targetJointOrientZ': 'jointOrientZ',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintRotateOrder': 'rotateOrder',
        'constraintJointOrientX': 'jointOrientX',
        'constraintJointOrientY': 'jointOrientY',
        'constraintJointOrientZ': 'jointOrientZ',
        'scaleCompensate': 'segmentScaleCompensate',
        'inverseScaleX': 'inverseScaleX',
        'inverseScaleY': 'inverseScaleY',
        'inverseScaleZ': 'inverseScaleZ',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Enums
    InterpType = InterpType
    # endregion

    # region Attributes
    interpType = mpyattribute.MPyAttribute('interpType')
    offset = mpyattribute.MPyAttribute('offset')
    offsetX = mpyattribute.MPyAttribute('offsetX')
    offsetY = mpyattribute.MPyAttribute('offsetY')
    offsetZ = mpyattribute.MPyAttribute('offsetZ')
    restRotate = mpyattribute.MPyAttribute('restRotate')
    restRotateX = mpyattribute.MPyAttribute('restRotateX')
    restRotateY = mpyattribute.MPyAttribute('restRotateY')
    restRotateZ = mpyattribute.MPyAttribute('restRotateZ')
    # endregion

    # region Methods
    def addTargets(self, targets, **kwargs):
        """
        Adds a list of new targets to this constraint.

        :type targets: List[transformmixin.TransformMixin]
        :key maintainOffset: bool
        :rtype: int
        """

        # Call parent method
        #
        super(OrientConstraintMixin, self).addTargets(targets, **kwargs)

        # Evaluate target count
        #
        numTargets = len(targets)

        if numTargets > 1:

            self.interpType = kwargs.get('interpType', self.InterpType.SHORTEST)

    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        # Reset offset
        #
        self.offset = [0.0, 0.0, 0.0]

        # Get current constraint matrix
        #
        constraintAngles = self.getAttr('constraintRotate', convertUnits=False)
        constraintRotateOrder = self.getAttr('constraintRotateOrder')
        constraintEulerRotation = om.MEulerRotation([x.asRadians() for x in constraintAngles], order=constraintRotateOrder)

        constraintMatrix = constraintEulerRotation.asMatrix()

        # Update offset
        #
        restAngles = self.getAttr('restRotate', convertUnits=False)
        restEulerRotation = om.MEulerRotation([x.asRadians() for x in restAngles], order=constraintRotateOrder)

        offsetMatrix = restEulerRotation.asMatrix() * constraintMatrix.inverse()
        offsetEulerRotation = transformutils.decomposeTransformMatrix(offsetMatrix, rotateOrder=constraintRotateOrder)[1]

        self.offsetX = math.degrees(offsetEulerRotation.x)
        self.offsetY = math.degrees(offsetEulerRotation.y)
        self.offsetZ = math.degrees(offsetEulerRotation.z)
    # endregion
