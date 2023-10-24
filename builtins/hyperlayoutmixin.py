from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils
from . import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class HyperLayoutMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with hyper layouts.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kHyperLayout

    def __contains__(self, item):
        """
        Private method that evaluates if the supplied object belongs to this hyper layout.

        :type item: om.MObject
        :rtype: bool
        """

        return self.hasMember(item)
    # endregion

    # region Methods
    def hasMember(self, dependNode):
        """
        Evaluates if the supplied dependency node belongs to this hyper layout.

        :type dependNode: om.MObject
        :rtype: bool
        """

        return self.getMemberIndex(dependNode) is not None

    def members(self):
        """
        Returns a list of members belonging to this hyper layout.

        :rtype: List[mpy.mpynode.MPyNode]
        """

        return list(self.iterMembers())

    def getMemberIndex(self, dependNode):
        """
        Returns the index for the given member.
        If this node does not belong to this hyper layout then none is returned!

        :type dependNode: om.MObject
        :rtype: int
        """

        # Find connected message plug
        #
        plug = self.findConnectedMessage(dependNode, attribute=self.attribute('dependNode'))

        if plug is not None:
            
            return plug.parent().logicalIndex()

        else:

            return None

    def getNextAvailableMemberIndex(self):
        """
        Returns the next available member index.

        :rtype: int
        """

        return self.getNextAvailableConnection('hyperPosition', child=self.attribute('dependNode'))

    def iterMembers(self):
        """
        Returns a generator that yields members from this layout.

        :rtype: Iterator[mpy.mpynode.MPyNode]
        """

        # Iterate through hyper positions
        #
        for hyperPosition in self.iterHyperPositions():

            # Check if hyper position has a dependency node
            #
            if hyperPosition.hasDependNode():

                yield self.scene(hyperPosition.dependNode())

            else:

                continue

    def addMember(self, dependNode):
        """
        Adds a new dependency node to this hyper layout.

        :type dependNode: om.MObject
        :rtype: bool
        """

        # Check if member has already been added
        #
        if self.hasMember(dependNode) or dependNode == self.object():

            return False

        # Get message plugs
        #
        index = self.getNextAvailableMemberIndex()
        destination = self.findPlug('hyperPosition[%s].dependNode' % index)

        fnDependNode = om.MFnDependencyNode(dependNode)
        source = fnDependNode.findPlug('message', True)

        # Connect plugs
        #
        self.connectPlugs(source, destination)
        return True

    def addMembers(self, dependNodes):
        """
        Adds a list of dependency nodes to this hyper layout.

        :type dependNodes: List[om.MObject]
        :rtype: None
        """

        for dependNode in dependNodes:

            self.addMember(dependNode)

    def removeMember(self, dependNode):
        """
        Removes a dependency node from this hyper layout.

        :type dependNode: om.MObject
        :rtype: bool
        """

        # Get member index
        #
        fnDependNode = om.MFnDependencyNode(dependNode)
        index = self.getMemberIndex(dependNode)

        if index is None:

            log.warning('"%s" node is not a member of this container!' % fnDependNode.name())
            return False

        # Get message plugs
        #
        source = fnDependNode.findPlug('message')
        destination = self.findPlug('hyperPosition[%s].dependNode' % index)

        # Disconnect plugs
        #
        self.disconnectPlugs(source, destination)
        return True

    def removeMembers(self, dependNodes):
        """
        Removes a list of dependency nodes from this hyper layout.

        :type dependNodes: list[om.MObject]
        :rtype: None
        """

        for dependNode in dependNodes:

            self.removeMember(dependNode)

    def deleteMembers(self):
        """
        Deletes all the members derived from this hyper layout.

        :rtype: None
        """

        # Iterate through hyper positions
        #
        for hyperPosition in self.iterHyperPositions():

            # Check if hyper position has depend node
            #
            if not hyperPosition.hasDependNode():

                continue

            # Delete dependency node
            #
            dependNode = hyperPosition.dependNode()
            dagutils.deleteNode(dependNode)

    def hyperPositions(self):
        """
        Returns a list of hyper positions for this hyper layout.

        :rtype: List[HyperPosition]
        """

        return list(self.iterHyperPositions())

    def iterHyperPositions(self):
        """
        Returns a generator that yields hyper positions.

        :rtype: Iterator[HyperPosition]
        """

        # Iterate through plug elements
        #
        plug = self.findPlug('hyperPosition')
        numElements = plug.evaluateNumElements()

        for physicalIndex in range(numElements):

            element = plug.elementByPhysicalIndex(physicalIndex)
            logicalIndex = element.logicalIndex()

            yield HyperPosition(self, index=logicalIndex)

    def resetHyperPositions(self):
        """
        Removes all existing hyper position plug indices.
        Sadly this node will keep inserting new nodes from the last known index.
        Must be something under the hood tracking this.

        :rtype: None
        """

        # Get existing array indices
        #
        plug = self.findPlug('hyperPosition')
        elements = plug.getExistingArrayAttributeIndices()

        # Remove indices from plug
        #
        self.removePlugIndices(plug, elements)
    # endregion


class HyperPosition(object):
    """
    Base class used to interface with container members.
    """

    # region Dunderscores
    __slots__ = ('_hyperLayout', '_index')

    def __init__(self, hyperLayout, **kwargs):
        """
        Inherited method called after a new instance has been created.

        :type hyperLayout: HyperLayoutMixin
        :rtype: None
        """

        # Call parent method
        #
        super(HyperPosition, self).__init__()

        # Declare class variables
        #
        self._hyperLayout = hyperLayout.weakReference()
        self._index = kwargs.get('index', 0)
    # endregion

    # region Properties
    @property
    def hyperLayout(self):
        """
        Getter method used to retrieve the associated hyper layout for this hyper position.

        :rtype: HyperLayoutMixin
        """

        return self._hyperLayout()

    @property
    def index(self):
        """
        Getter method used to retrieve the index for this hyper position.

        :rtype: int
        """

        return self._index
    # endregion

    # region Methods
    def plug(self):
        """
        Returns the compound plug element for this publised node info.

        :rtype: om.MPlug
        """

        return self.hyperLayout.findPlug('hyperPosition[%s]' % self.index)

    def positionX(self):
        """
        Returns the x value for this member.

        :rtype: float
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].positionX' % self.index)

    def positionY(self):
        """
        Returns the y value for this member.

        :rtype: float
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].positionY' % self.index)

    def isCollapsed(self):
        """
        Returns the collapsed state for this member.

        :rtype: float
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].isCollapsed' % self.index)

    def isFreeform(self):
        """
        Returns the freeform state for this member.

        :rtype: bool
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].isFreeform' % self.index)

    def nodeVisualState(self):
        """
        Returns the node visual state for this member.

        :rtype: int
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].nodeVisualState' % self.index)

    def hasDependNode(self):
        """
        Checks if the dependency node at this hyper position is valid.

        :rtype: bool
        """

        return not self.hyperLayout.findPlug('hyperPosition[%s].dependNode' % self.index).source().isNull

    def dependNode(self):
        """
        Returns the dependency node associated with this member.

        :rtype: om.MObject
        """

        return self.hyperLayout.getAttr('hyperPosition[%s].dependNode' % self.index)

    def setDependNode(self, dependNode):
        """
        Returns the dependency node associated with this member.

        :type dependNode: om.MObject
        :rtype: None
        """

        self.hyperLayout.setAttr('hyperPosition[%s].dependNode' % self.index, dependNode)
    # endregion
