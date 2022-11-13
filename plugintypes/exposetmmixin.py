from maya.api import OpenMaya as om
from .. import mpyattribute
from . import maxformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MaxformMixin(maxformmixin.MaxformMixin):
    """
    Overload of TransformMixin that interfaces with expose transforms.
    """

    # region Dunderscores
    __plugin__ = 'exposeTm'
    # endregion

    # region Attributes
    exposeNode = mpyattribute.MPyAttribute('exposeNode')
    localReferenceNode = mpyattribute.MPyAttribute('localReferenceNode')
    useParent = mpyattribute.MPyAttribute('useParent')
    eulerXOrder = mpyattribute.MPyAttribute('eulerXOrder')
    eulerYOrder = mpyattribute.MPyAttribute('eulerYOrder')
    eulerZOrder = mpyattribute.MPyAttribute('eulerZOrder')
    stripNUScale = mpyattribute.MPyAttribute('stripNUScale')
    useTimeOffset = mpyattribute.MPyAttribute('useTimeOffset')
    timeOffset = mpyattribute.MPyAttribute('timeOffset')
    localPosition = mpyattribute.MPyAttribute('localPosition')
    localPositionX = mpyattribute.MPyAttribute('localPositionX')
    localPositionY = mpyattribute.MPyAttribute('localPositionY')
    localPositionZ = mpyattribute.MPyAttribute('localPositionZ')
    localEuler = mpyattribute.MPyAttribute('localEuler')
    localEulerX = mpyattribute.MPyAttribute('localEulerX')
    localEulerY = mpyattribute.MPyAttribute('localEulerY')
    localEulerZ = mpyattribute.MPyAttribute('localEulerZ')
    worldPosition = mpyattribute.MPyAttribute('worldPosition')
    worldPositionX = mpyattribute.MPyAttribute('worldPositionX')
    worldPositionY = mpyattribute.MPyAttribute('worldPositionY')
    worldPositionZ = mpyattribute.MPyAttribute('worldPositionZ')
    worldEuler = mpyattribute.MPyAttribute('worldEuler')
    worldEulerX = mpyattribute.MPyAttribute('worldEulerX')
    worldEulerY = mpyattribute.MPyAttribute('worldEulerY')
    worldEulerZ = mpyattribute.MPyAttribute('worldEulerZ')
    distance = mpyattribute.MPyAttribute('distance')
    angle = mpyattribute.MPyAttribute('angle')
    # endregion

    # region Methods
    @exposeNode.validateAndGetValue
    def exposeNode(self, exposeNode):
        """
        Validator method that returns an expose-node interface.

        :type exposeNode: om.MObject
        :rtype: transformmixin.TransformMixin
        """

        # Check for null objects
        #
        if not exposeNode.isNull():

            return self.pyFactory(exposeNode)

        else:

            return None

    @localReferenceNode.validateAndGetValue
    def localReferenceNode(self, localReferenceNode):
        """
        Validator method that returns a local-reference node interface.

        :type localReferenceNode: om.MObject
        :rtype: transformmixin.TransformMixin
        """

        # Check for null objects
        #
        if not localReferenceNode.isNull():

            return self.pyFactory(localReferenceNode)

        else:

            return None
    # endregion
