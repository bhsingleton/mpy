import math

from maya.api import OpenMaya as om
from enum import IntEnum
from dcc.python import stringutils
from dcc.maya.libs import transformutils
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class WorldUpType(IntEnum):
    """
    Enum class of all available world-up types.
    """

    SCENE = 0
    OBJECT = 1
    OBJECT_ROTATION = 2
    VECTOR = 3
    NONE = 4


class AimConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with orient constraints.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kAimConstraint

    __targets__ = {
        'targetTranslateX': 'translateX',
        'targetTranslateY': 'translateY',
        'targetTranslateZ': 'translateZ',
        'targetRotatePivotX': 'rotatePivotX',
        'targetRotatePivotY': 'rotatePivotY',
        'targetRotatePivotZ': 'rotatePivotZ',
        'targetRotateTranslateX': 'rotatePivotTranslateX',
        'targetRotateTranslateY': 'rotatePivotTranslateY',
        'targetRotateTranslateZ': 'rotatePivotTranslateZ',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ',
        'constraintRotatePivotX': 'rotatePivotX',
        'constraintRotatePivotY': 'rotatePivotY',
        'constraintRotatePivotZ': 'rotatePivotZ',
        'constraintRotateTranslateX': 'rotatePivotTranslateX',
        'constraintRotateTranslateY': 'rotatePivotTranslateY',
        'constraintRotateTranslateZ': 'rotatePivotTranslateZ',
        'constraintRotateOrder': 'rotateOrder',
        'constraintJointOrientX': 'jointOrientX',
        'constraintJointOrientY': 'jointOrientY',
        'constraintJointOrientZ': 'jointOrientZ',
        'inverseScaleX': 'inverseScaleX',
        'inverseScaleY': 'inverseScaleY',
        'inverseScaleZ': 'inverseScaleZ',
        'scaleCompensate': 'segmentScaleCompensate',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Enums
    WorldUpType = WorldUpType
    # endregion

    # region Attributes
    aimVector = mpyattribute.MPyAttribute('aimVector')
    aimVectorX = mpyattribute.MPyAttribute('aimVectorX')
    aimVectorY = mpyattribute.MPyAttribute('aimVectorY')
    aimVectorZ = mpyattribute.MPyAttribute('aimVectorZ')
    upVector = mpyattribute.MPyAttribute('upVector')
    upVectorX = mpyattribute.MPyAttribute('upVectorX')
    upVectorY = mpyattribute.MPyAttribute('upVectorY')
    upVectorZ = mpyattribute.MPyAttribute('upVectorZ')
    worldUpType = mpyattribute.MPyAttribute('worldUpType')  # scene, object, objectRotation, vector, none
    worldUpVector = mpyattribute.MPyAttribute('worldUpVector')
    worldUpVectorX = mpyattribute.MPyAttribute('worldUpVectorX')
    worldUpVectorY = mpyattribute.MPyAttribute('worldUpVectorY')
    worldUpVectorZ = mpyattribute.MPyAttribute('worldUpVectorZ')
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
    def setConstraintObject(self, constraintObject, **kwargs):
        """
        Updates the constraint object for this instance.

        :type constraintObject: mpy.builtins.transformmixin.TransformMixin
        :key aimVector: Tuple[float, float, float]
        :key upVector: Tuple[float, float, float]
        :key worldUpType: int
        :key worldUpVector: Tuple[float, float, float]
        :key worldUpObject: Union[mpy.builtins.transformmixin.TransformMixin, None]
        :rtype: None
        """

        # Call parent method
        #
        super(AimConstraintMixin, self).setConstraintObject(constraintObject, **kwargs)

        # Update aim properties
        #
        self.aimVector = kwargs.get('aimVector', (1.0, 0.0, 0.0))
        self.upVector = kwargs.get('upVector', (0.0, 1.0, 0.0))
        self.worldUpType = kwargs.get('worldUpType', 3)  # Vector
        self.worldUpVector = kwargs.get('worldUpVector', (0.0, 1.0, 0.0))

        # Check if a world-up object was supplied
        #
        worldUpObject = kwargs.get('worldUpObject', None)

        if worldUpObject is not None:

            self.setWorldUpObject(worldUpObject)

    def worldUpObject(self):
        """
        Returns the world-up object for this constraint.

        :rtype: mpynode.builtins.transformmixin.TransformMixin
        """

        plug = self.findPlug('worldUpMatrix')
        source = plug.source()

        if not source.isNull():

            return self.scene(source.node())

        else:

            return None

    def setWorldUpObject(self, node):
        """
        Updates the world-up object for this constraint.

        :type node: mpynode.builtins.transformmixin.TransformMixin
        :rtype: None
        """

        node.connectPlugs(f'worldMatrix[{node.instanceNumber()}]', self.findPlug('worldUpMatrix'), force=True)

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
