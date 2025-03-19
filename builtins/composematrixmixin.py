from maya.api import OpenMaya as om
from enum import IntEnum
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ComposeMatrixMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with compose matrix nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kComposeMatrix
    # endregion

    # region Attributes
    inputTranslate = mpyattribute.MPyAttribute('inputTranslate')
    inputTranslateX = mpyattribute.MPyAttribute('inputTranslateX')
    inputTranslateY = mpyattribute.MPyAttribute('inputTranslateY')
    inputTranslateZ = mpyattribute.MPyAttribute('inputTranslateZ')
    useEulerRotation = mpyattribute.MPyAttribute('useEulerRotation')
    inputRotate = mpyattribute.MPyAttribute('inputRotate')
    inputRotateX = mpyattribute.MPyAttribute('inputRotateX')
    inputRotateY = mpyattribute.MPyAttribute('inputRotateY')
    inputRotateZ = mpyattribute.MPyAttribute('inputRotateZ')
    inputRotateOrder = mpyattribute.MPyAttribute('inputRotateOrder')
    inputQuat = mpyattribute.MPyAttribute('inputQuat')
    inputQuatX = mpyattribute.MPyAttribute('inputQuatX')
    inputQuatY = mpyattribute.MPyAttribute('inputQuatY')
    inputQuatZ = mpyattribute.MPyAttribute('inputQuatZ')
    inputQuatW = mpyattribute.MPyAttribute('inputQuatW')
    inputScale = mpyattribute.MPyAttribute('inputScale')
    inputScaleX = mpyattribute.MPyAttribute('inputScaleX')
    inputScaleY = mpyattribute.MPyAttribute('inputScaleY')
    inputScaleZ = mpyattribute.MPyAttribute('inputScaleZ')
    inputShear = mpyattribute.MPyAttribute('inputShear')
    inputShearX = mpyattribute.MPyAttribute('inputShearX')
    inputShearY = mpyattribute.MPyAttribute('inputShearY')
    inputShearZ = mpyattribute.MPyAttribute('inputShearZ')
    outputMatrix = mpyattribute.MPyAttribute('outputMatrix')
    # endregion

    # region Methods
    def copyMatrix(self, matrix, rotateOrder=om.MEulerRotation.kXYZ):
        """
        Copies the supplied transform matrix to the corresponding input attributes.

        :type matrix: om.MMatrix
        :type rotateOrder: int
        :rtype: None
        """

        translation, eulerRotation, scale = transformutils.decomposeTransformMatrix(matrix, rotateOrder=rotateOrder)

        self.inputTranslate = translation
        self.useEulerRotation = True
        self.inputRotateOrder = rotateOrder
        self.inputRotate = eulerRotation
        self.inputScale = scale
    # endregion
