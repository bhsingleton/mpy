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

    def setLocalMatrix(self, localMatrix, **kwargs):
        """
        Updates the local matrix for this locator.

        :type localMatrix: om.MMatrix
        :key skipPosition: bool
        :key skipRotate: bool
        :key skipScale: bool
        :rtype: None
        """

        # Decompose local matrix
        #
        localPosition, localRotate, localScale = transformutils.decomposeTransformMatrix(localMatrix)

        # Check if position should be skipped
        #
        skipPosition = kwargs.get('skipPosition', False)

        if not skipPosition:

            self.setAttr('localPosition', localPosition)

        # Check if rotation should be skipped
        #
        skipRotate = kwargs.get('skipRotate', False)

        if not skipRotate and self.hasAttr('localRotate'):

            self.setAttr('localRotate', list(map(math.degrees, localRotate)))

        # Check if scale should be skipped
        #
        skipScale = kwargs.get('skipScale', False)

        if not skipScale:

            self.setAttr('localScale', localScale)

    def resetLocalMatrix(self):
        """
        Resets the local matrix for this locator.

        :rtype: None
        """

        self.setLocalMatrix(om.MMatrix.kIdentity)
    # endregion
