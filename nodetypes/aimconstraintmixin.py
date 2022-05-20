from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AimConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of ConstraintMixin that interfaces with orient constraints.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kAimConstraint

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
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        pass
    # endregion
