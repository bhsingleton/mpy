from maya.api import OpenMaya as om
from enum import Enum
from dcc.naming import namingutils
from . import dependencymixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


Side = Enum('Side', {'Center': 0, 'Left': 1, 'Right': 2, 'None': 3})


class ControllerMixin(dependencymixin.DependencyMixin):
    """
    Overload of DependencyMixin class used to interface with controller tags.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kControllerTag
    # endregion

    # region Attributes
    controllerObject = mpyattribute.MPyAttribute('controllerObject')
    cycleWalkSibling = mpyattribute.MPyAttribute('cycleWalkSibling')
    parent = mpyattribute.MPyAttribute('parent')
    children = mpyattribute.MPyAttribute('children')
    prepopulate = mpyattribute.MPyAttribute('prepopulate')
    parentprepopulate = mpyattribute.MPyAttribute('parentprepopulate')
    side = mpyattribute.MPyAttribute('side')
    type = mpyattribute.MPyAttribute('type')
    otherType = mpyattribute.MPyAttribute('otherType')
    mirrorTranslate = mpyattribute.MPyAttribute('mirrorTranslate')
    mirrorRotate = mpyattribute.MPyAttribute('mirrorRotate')
    visibilityMode = mpyattribute.MPyAttribute('visibilityMode')
    #

    # region Methods
    def sibling(self):
        """
        Returns the sibling for this controller.
        If this transform has no sibling then none is returned!

        :rtype: mpynode.MPyNode
        """

        # Get sibling's UUID
        #
        uuid = om.MUuid(self.getAttr('sibling'))

        if uuid.valid():

            self.pyFactory.getNodeByUuid(uuid, referenceNode=self.getAssociatedReferenceNode())

        else:

            return None

    def hasSibling(self):
        """
        Checks if this controller has a sibling.

        :rtype: bool
        """

        return self.sibling() is not None

    def findSibling(self):
        """
        Finds the sibling for this node that transforms can be mirrored to.

        :rtype: TransformMixin
        """

        # Check if sibling already exists
        #
        if self.hasSibling():

            return self.sibling()

        # Mirror this controller name
        #
        name = self.controllerObject().displayName()
        mirrorName = namingutils.mirrorName(name)

        return self.pyFactory.getNodeByName(mirrorName)

    def setSibling(self, sibling):
        """
        Setter method used to update the sibling UUID.

        :type sibling: mpynode.MPyNode
        :rtype: None
        """

        self.setAttr('sibling', sibling.uuid().asString())
    # endregion
