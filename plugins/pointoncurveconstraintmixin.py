import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from enum import IntEnum
from .. import mpyattribute
from ..builtins import constraintmixin

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
        'constraintJointOrientX': 'jointOrientX',
        'constraintJointOrientY': 'jointOrientY',
        'constraintJointOrientZ': 'jointOrientZ',
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

    # region Enums
    WorldUpType = WorldUpType
    # endregion

    # region Attributes
    parameter = mpyattribute.MPyAttribute('parameter')
    useFraction = mpyattribute.MPyAttribute('useFraction')
    loop = mpyattribute.MPyAttribute('loop')
    forwardVector = mpyattribute.MPyAttribute('forwardVector')
    forwardVectorX = mpyattribute.MPyAttribute('forwardVectorX')
    forwardVectorY = mpyattribute.MPyAttribute('forwardVectorY')
    forwardVectorZ = mpyattribute.MPyAttribute('forwardVectorZ')
    upVector = mpyattribute.MPyAttribute('upVector')
    upVectorX = mpyattribute.MPyAttribute('upVectorX')
    upVectorY = mpyattribute.MPyAttribute('upVectorY')
    upVectorZ = mpyattribute.MPyAttribute('upVectorZ')
    worldUpType = mpyattribute.MPyAttribute('worldUpType')  # scene, object, objectRotation, vector, none
    worldUpVector = mpyattribute.MPyAttribute('worldUpVector')
    worldUpVectorX = mpyattribute.MPyAttribute('worldUpVectorX')
    worldUpVectorY = mpyattribute.MPyAttribute('worldUpVectorY')
    worldUpVectorZ = mpyattribute.MPyAttribute('worldUpVectorZ')
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
        super(PointOnCurveConstraintMixin, self).setConstraintObject(constraintObject, **kwargs)

        # Update aim properties
        #
        self.parameter = kwargs.get('parameter', 0.0)
        self.useFraction = kwargs.get('useFraction', False)
        self.loop = kwargs.get('loop', False)
        self.twist = kwargs.get('twist', 0.0)
        self.forwardVector = kwargs.get('forwardVector', (1.0, 0.0, 0.0))
        self.upVector = kwargs.get('upVector', (0.0, 1.0, 0.0))
        self.worldUpType = kwargs.get('worldUpType', 0)  # Vector
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
