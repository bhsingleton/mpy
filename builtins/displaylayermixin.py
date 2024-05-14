from maya.api import OpenMaya as om
from dcc.maya.libs import plugutils
from . import dependencymixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DisplayLayerMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with display layers.
    """

    # region Attributes
    displayInfo = mpyattribute.MPyAttribute('displayInfo')
    displayType = mpyattribute.MPyAttribute('displayType')
    levelOfDetail = mpyattribute.MPyAttribute('levelOfDetail')
    shading = mpyattribute.MPyAttribute('shading')
    texturing = mpyattribute.MPyAttribute('texturing')
    playback = mpyattribute.MPyAttribute('playback')
    enabled = mpyattribute.MPyAttribute('enabled')
    visibility = mpyattribute.MPyAttribute('visibility')
    hideOnPlayback = mpyattribute.MPyAttribute('hideOnPlayback')
    overrideRGBColors = mpyattribute.MPyAttribute('overrideRGBColors')
    color = mpyattribute.MPyAttribute('color')
    overrideColorRGB = mpyattribute.MPyAttribute('overrideColorRGB')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kDisplayLayer

    def __contains__(self, item):
        """
        Private method that evaluates if the supplied object belongs to this layer.

        :type item: om.MObject
        :rtype: bool
        """

        return self.hasNode(item)

    def __getitem__(self, index):
        """
        Private method that returns an indexed node from this layer.

        :type index: int
        :rtype: om.MObject
        """

        return self.nodes()[index]

    def __iter__(self):
        """
        Private method that returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        return self.iterNodes()

    def __len__(self):
        """
        Private method that evaluates the number of nodes belonging to this layer.

        :rtype: int
        """

        return len(self.nodes())
    # endregion

    # region Methods
    def hasNode(self, node):
        """
        Evaluates if the supplied node belongs to this layer.

        :type node: Union[om.MObject, om.MDagPath, dependencymixin.DependencyMixin]
        :rtype: bool
        """

        return node in self.nodes()

    def iterNodes(self):
        """
        Returns a generator that yields nodes belonging to this layer.

        :rtype: iter
        """

        plug = self.findPlug('drawInfo')
        destinations = plug.destinations()

        for destination in destinations:

            node = destination.node()

            if not node.isNull():

                yield self.scene(node)

            else:

                continue

    def nodes(self):
        """
        Returns a list of nodes belonging to this layer.

        :rtype: List[om.MObject]
        """

        return list(self.iterNodes())

    def addNode(self, node):
        """
        Adds the supplied node to this layer.

        :type node: om.MObject
        :rtype: None
        """

        source = self.findPlug('drawInfo')
        destination = plugutils.findPlug(node, 'drawOverride')

        plugutils.connectPlugs(source, destination, force=True)

    def addNodes(self, nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: List[om.MObject]
        :rtype: None
        """

        for node in nodes:

            self.addNode(node)

    def removeNode(self, node):
        """
        Removes the supplied node from this layer.

        :type node: om.MObject
        :rtype: None
        """

        if self.hasNode(node):

            plug = plugutils.findPlug(node, 'drawOverride')
            plugutils.breakConnections(plug, source=True, destination=False)

    def removeNodes(self, nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: List[om.MObject]
        :rtype: None
        """

        for node in nodes:

            self.removeNode(node)

    def clearNodes(self):
        """
        Removes all nodes from this layer.

        :rtype: None
        """

        nodes = self.nodes()

        for node in reversed(nodes):

            self.removeNode(node)
    # endregion
