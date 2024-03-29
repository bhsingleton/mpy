from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import constraintmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransformConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with transform constraints.
    """

    # region Dunderscores
    __plugin__ = 'transformConstraint'

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
        'targetRotateX': 'rotateX',
        'targetRotateY': 'rotateY',
        'targetRotateZ': 'rotateZ',
        'targetRotateOrder': 'rotateOrder',
        'targetJointOrientX': 'jointOrientX',
        'targetJointOrientY': 'jointOrientY',
        'targetJointOrientZ': 'jointOrientZ',
        'targetScaleX': 'scaleX',
        'targetScaleY': 'scaleY',
        'targetScaleZ': 'scaleZ',
        'targetScalePivotX': 'scalePivotX',
        'targetScalePivotY': 'scalePivotY',
        'targetScalePivotZ': 'scalePivotZ',
        'targetScaleTranslateX': 'scalePivotTranslateX',
        'targetScaleTranslateY': 'scalePivotTranslateY',
        'targetScaleTranslateZ': 'scalePivotTranslateZ',
        'targetScaleCompensate': 'segmentScaleCompensate',
        'targetInverseScale': 'inverseScale',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintRotatePivotX': 'rotatePivotX',
        'constraintRotatePivotY': 'rotatePivotY',
        'constraintRotatePivotZ': 'rotatePivotZ',
        'constraintRotatePivotTranslateX': 'rotatePivotTranslateX',
        'constraintRotatePivotTranslateY': 'rotatePivotTranslateY',
        'constraintRotatePivotTranslateZ': 'rotatePivotTranslateZ',
        'constraintRotateOrder': 'rotateOrder',
        'constraintJointOrientX': 'jointOrientX',
        'constraintJointOrientY': 'jointOrientY',
        'constraintJointOrientZ': 'jointOrientZ',
        'constraintScalePivotX': 'scalePivotX',
        'constraintScalePivotY': 'scalePivotY',
        'constraintScalePivotZ': 'scalePivotZ',
        'constraintScalePivotTranslateX': 'scalePivotTranslateX',
        'constraintScalePivotTranslateY': 'scalePivotTranslateY',
        'constraintScalePivotTranslateZ': 'scalePivotTranslateZ',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ',
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ',
        'constraintScaleX': 'scaleX',
        'constraintScaleY': 'scaleY',
        'constraintScaleZ': 'scaleZ'
    }
    # endregion

    # region Attributes
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
    restRotate = mpyattribute.MPyAttribute('restRotate')
    restRotateX = mpyattribute.MPyAttribute('restRotateX')
    restRotateY = mpyattribute.MPyAttribute('restRotateY')
    restRotateZ = mpyattribute.MPyAttribute('restRotateZ')
    restScale = mpyattribute.MPyAttribute('restScale')
    restScaleX = mpyattribute.MPyAttribute('restScaleX')
    restScaleY = mpyattribute.MPyAttribute('restScaleY')
    restScaleZ = mpyattribute.MPyAttribute('restScaleZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        restMatrix = self.worldRestMatrix()

        for target in self.iterTargets():

            node = target.targetObject()
            worldMatrix = node.worldMatrix()
            offsetMatrix = restMatrix * worldMatrix.inverse()

            translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(offsetMatrix)
            target.setTargetOffsetTranslate(translation)
            target.setTargetOffsetRotate(eulerRotation)
    # endregion
