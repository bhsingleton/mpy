from maya.api import OpenMaya as om
from dcc.maya.libs import plugutils
from .. import mpyattribute
from ..nodetypes import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PRSMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with prs nodes.
    """

    # region Attributes
    position = mpyattribute.MPyAttribute('position')
    x_position = mpyattribute.MPyAttribute('x_position')
    y_position = mpyattribute.MPyAttribute('y_position')
    z_position = mpyattribute.MPyAttribute('z_position')
    axisOrder = mpyattribute.MPyAttribute('axisOrder')
    rotation = mpyattribute.MPyAttribute('rotation')
    x_rotation = mpyattribute.MPyAttribute('x_rotation')
    y_rotation = mpyattribute.MPyAttribute('y_rotation')
    z_rotation = mpyattribute.MPyAttribute('z_rotation')
    scale = mpyattribute.MPyAttribute('scale')
    x_scale = mpyattribute.MPyAttribute('x_scale')
    y_scale = mpyattribute.MPyAttribute('y_scale')
    z_scale = mpyattribute.MPyAttribute('z_scale')
    value = mpyattribute.MPyAttribute('value')
    # endregion

    # region Dunderscores
    __plugin__ = 'prs'
    # endregion

    # region Methods
    def getAssociatedTransform(self):
        """
        Returns the transform node associated with this node.

        :rtype: Union[mpy.plugintypes.maxformmixin.MaxformMixin, None]
        """

        connections = self.findPlug('value').destinations()
        numConnections = len(connections)

        if numConnections == 1:

            return self.scene(connections[0].node())

        else:

            return None

    def getPositionController(self):
        """
        Returns the node driving the position attribute.
        If no connections are found then none is returned instead!

        :rtype: Union[dependencymixin.DependencyMixin, None]
        """

        nodes = plugutils.getConnectedNodes(self.findPlug('position'))
        numNodes = len(nodes)

        if numNodes == 3:

            return self.scene(nodes[0])

        else:

            return None

    def getRotationController(self):
        """
        Returns the node driving the rotation attribute.
        If no connections are found then none is returned instead!

        :rtype: Union[dependencymixin.DependencyMixin, None]
        """

        nodes = plugutils.getConnectedNodes(self.findPlug('rotation'))
        numNodes = len(nodes)

        if numNodes == 3:

            return self.scene(nodes[0])

        else:

            return None

    def getScaleController(self):
        """
        Returns the node driving the scale attribute.
        If no connections are found then none is returned instead!

        :rtype: Union[dependencymixin.DependencyMixin, None]
        """

        nodes = plugutils.getConnectedNodes(self.findPlug('scale'))
        numNodes = len(nodes)

        if numNodes == 3:

            return self.scene(nodes[0])

        else:

            return None
    # endregion
