from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PointConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with point constraints.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kPointConstraint

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
        'constraintRotatePivotX': 'rotatePivotX',
        'constraintRotatePivotY': 'rotatePivotY',
        'constraintRotatePivotZ': 'rotatePivotZ',
        'constraintRotateTranslateX': 'rotatePivotTranslateX',
        'constraintRotateTranslateY': 'rotatePivotTranslateY',
        'constraintRotateTranslateZ': 'rotatePivotTranslateZ',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ'
    }
    # endregion

    # region Attributes
    offset = mpyattribute.MPyAttribute('offset')
    offsetX = mpyattribute.MPyAttribute('offsetX')
    offsetY = mpyattribute.MPyAttribute('offsetY')
    offsetZ = mpyattribute.MPyAttribute('offsetZ')
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        # Reset offset
        #
        self.offset = [0.0, 0.0, 0.0]

        # Get constraint matrix
        #
        constraintTranslate = self.getAttr('constraintTranslate')
        constraintMatrix = transformutils.createTranslateMatrix(constraintTranslate)

        # Update offset
        #
        restMatrix = self.restMatrix()
        offsetMatrix = restMatrix * constraintMatrix.inverse()
        offsetTranslate = transformutils.breakMatrix(offsetMatrix)[3]

        self.offset = offsetTranslate
    # endregion
