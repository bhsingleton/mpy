from maya.api import OpenMaya as om
from dcc.maya.libs import plugutils
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKControlMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with ik controllers.
    """

    # region Attributes
    rotationXActive = mpyattribute.MPyAttribute('rotationXActive')
    rotationXLimited = mpyattribute.MPyAttribute('rotationXLimited')
    rotationXLowerLimit = mpyattribute.MPyAttribute('rotationXLowerLimit')
    rotationXUpperLimit = mpyattribute.MPyAttribute('rotationXUpperLimit')
    rotationYActive = mpyattribute.MPyAttribute('rotationYActive')
    rotationYLimited = mpyattribute.MPyAttribute('rotationYLimited')
    rotationYLowerLimit = mpyattribute.MPyAttribute('rotationYLowerLimit')
    rotationYUpperLimit = mpyattribute.MPyAttribute('rotationYUpperLimit')
    rotationZActive = mpyattribute.MPyAttribute('rotationZActive')
    rotationZLimited = mpyattribute.MPyAttribute('rotationZLimited')
    rotationZLowerLimit = mpyattribute.MPyAttribute('rotationZLowerLimit')
    rotationZUpperLimit = mpyattribute.MPyAttribute('rotationZUpperLimit')
    preferredRotation = mpyattribute.MPyAttribute('preferredRotation')
    preferredRotationX = mpyattribute.MPyAttribute('preferredRotationX')
    preferredRotationY = mpyattribute.MPyAttribute('preferredRotationY')
    preferredRotationZ = mpyattribute.MPyAttribute('preferredRotationZ')
    # endregion

    # region Dunderscores
    __plugin__ = 'ikControl'
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

    def getFKSubController(self):
        """
        Returns the FK sub-controller.
        If no controller is found then none is returned instead!

        :rtype: Union[dependencymixin.DependencyMixin, None]
        """

        connections = self.findPlug('fkSubControl').destinations()
        numConnections = len(connections)

        if numConnections == 1:

            return self.scene(connections[0].node())

        else:

            return None
    # endregion
