from maya.api import OpenMaya as om
from dcc.maya.libs import plugutils
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKChainControlMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with ik-chain controllers.
    """

    # region Attributes
    enabled = mpyattribute.MPyAttribute('enabled')
    forwardAxis = mpyattribute.MPyAttribute('forwardAxis')
    forwardAxisFlip = mpyattribute.MPyAttribute('forwardAxisFlip')
    upAxis = mpyattribute.MPyAttribute('upAxis')
    upAxisFlip = mpyattribute.MPyAttribute('upAxisFlip')
    swivelAngle = mpyattribute.MPyAttribute('swivelAngle')
    useVHTarget = mpyattribute.MPyAttribute('useVHTarget')
    # endregion

    # region Dunderscores
    __plugin__ = 'ikChainControl'
    # endregion

    # region Methods
    def getAssociatedTransform(self):
        """
        Returns the transform node associated with this node.

        :rtype: Union[mpy.plugins.maxformmixin.MaxformMixin, None]
        """

        connections = self.findPlug('value').destinations()
        numConnections = len(connections)

        if numConnections == 1:

            return self.scene(connections[0].node())

        else:

            return None

    def getIKGoal(self):
        """
        Returns the transform controller.
        If no controller is found then None is returned instead!

        :rtype: Union[dependencymixin.DependencyMixin, None]
        """

        connections = self.findPlug('ikGoal').destinations()
        numConnections = len(connections)

        if numConnections == 1:

            return self.scene(connections[0].node())

        else:

            return None
    # endregion
