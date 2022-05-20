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
    Overload of ShapeMixin used to interface with locators inside the scene file.
    """

    # region Dunderscores
    __apitype__ = (om.MFn.kLocator, om.MFn.kPluginLocatorNode)
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

        localPositionMatrix = transformutils.createTranslateMatrix(self.localPosition)
        localRotateMatrix = om.MMatrix.kIdentity
        localScaleMatrix = transformutils.createScaleMatrix(self.localScale)

        if self.hasAttr('localRotate'):

            localRotateMatrix = transformutils.createRotationMatrix(self.localRotate)

        return localScaleMatrix * localRotateMatrix * localPositionMatrix

    def setLocalMatrix(self, localMatrix):
        """
        Updates the local matrix for this locator.

        :type localMatrix: om.MMatrix
        :rtype: None
        """

        localPosition, localRotate, localScale = transformutils.decomposeTransformMatrix(localMatrix)

        self.localPosition = localPosition
        self.localScale = localScale

        if self.hasAttr('localRotate'):

            self.localRotateX = math.degrees(localRotate.x)
            self.localRotateY = math.degrees(localRotate.y)
            self.localRotateZ = math.degrees(localRotate.z)
    # endregion
