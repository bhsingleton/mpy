import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import shapemixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LocatorMixin(shapemixin.ShapeMixin):
    """
    Overload of `ShapeMixin` that interfaces with locator nodes.
    """

    # region Dunderscores
    __api_type__ = (om.MFn.kLocator, om.MFn.kPluginLocatorNode)
    # endregion

    # region Attributes
    localPosition = mpyattribute.MPyAttribute('localPosition')
    localPositionX = mpyattribute.MPyAttribute('localPositionX')
    localPositionY = mpyattribute.MPyAttribute('localPositionY')
    localPositionZ = mpyattribute.MPyAttribute('localPositionZ')
    localRotate = mpyattribute.MPyAttribute('localRotate')
    localRotateX = mpyattribute.MPyAttribute('localRotateX')
    localRotateY = mpyattribute.MPyAttribute('localRotateY')
    localRotateZ = mpyattribute.MPyAttribute('localRotateZ')
    localScale = mpyattribute.MPyAttribute('localScale')
    localScaleX = mpyattribute.MPyAttribute('localScaleX')
    localScaleY = mpyattribute.MPyAttribute('localScaleY')
    localScaleZ = mpyattribute.MPyAttribute('localScaleZ')
    underWorldObject = mpyattribute.MPyAttribute('underWorldObject')
    worldPosition = mpyattribute.MPyAttribute('worldPosition')
    worldPositionX = mpyattribute.MPyAttribute('worldPositionX')
    worldPositionY = mpyattribute.MPyAttribute('worldPositionY')
    worldPositionZ = mpyattribute.MPyAttribute('worldPositionZ')
    # endregion

    # region Methods
    def localMatrix(self):
        """
        Returns the local matrix for this locator.

        :rtype: om.MMatrix
        """

        # Compose local matrix components
        #
        localPositionMatrix = transformutils.createTranslateMatrix(self.localPosition)
        localRotateMatrix = om.MMatrix.kIdentity
        localScaleMatrix = transformutils.createScaleMatrix(self.localScale)

        # Check if local rotation exists
        #
        if self.hasAttr('localRotate'):

            localRotateMatrix = transformutils.createRotationMatrix(self.localRotate)

        return localScaleMatrix * localRotateMatrix * localPositionMatrix

    def setLocalMatrix(self, localMatrix):
        """
        Updates the local matrix for this locator.

        :type localMatrix: om.MMatrix
        :rtype: None
        """

        # Update local position and scale
        #
        localPosition, localRotate, localScale = transformutils.decomposeTransformMatrix(localMatrix)

        self.setAttr('localPosition', localPosition)
        self.setAttr('localScale', localScale)

        # Check if local rotation exists
        #
        if self.hasAttr('localRotate'):

            self.setAttr('localRotate', list(map(math.degrees, localRotate)))
    # endregion
