import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PointOnPolyConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with point-on-poly constraints.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kPointOnPolyConstraint

    __targets__ = {
        'targetMesh': 'worldMesh'
    }

    __inputs__ = {
        'constraintRotatePivot': 'rotatePivot',
        'constraintRotateTranslate': 'rotatePivotTranslate',
        'constraintRotateOrder': 'rotateOrder',
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
