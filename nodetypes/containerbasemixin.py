import maya.cmds as mc
import maya.api.OpenMaya as om
import os

from PySide2 import QtGui
from six import string_types

from . import dependencymixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ContainerBaseMixin(dependencymixin.DependencyMixin):
    """
    Overload of DependencyMixin class used to interface with container nodes.
    """

    __apitype__ = om.MFn.kContainerBase

    hyperLayout = mpyattribute.MPyAttribute('hyperLayout')
    isCollapsed = mpyattribute.MPyAttribute('isCollapsed')
    blackBox = mpyattribute.MPyAttribute('blackBox')
    rmbCommand = mpyattribute.MPyAttribute('rmbCommand')
    templateName = mpyattribute.MPyAttribute('templateName')
    templatePath = mpyattribute.MPyAttribute('templatePath')
    iconName = mpyattribute.MPyAttribute('iconName')
    viewMode = mpyattribute.MPyAttribute('viewMode')
    templateVersion = mpyattribute.MPyAttribute('templateVersion')
    uiTreatment = mpyattribute.MPyAttribute('uiTreatment')
    customTreatment = mpyattribute.MPyAttribute('customTreatment')
    owner = mpyattribute.MPyAttribute('creator')
    creationDate = mpyattribute.MPyAttribute('creationDate')
    containerType = mpyattribute.MPyAttribute('containerType')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(ContainerBaseMixin, self).__init__(*args, **kwargs)

    def __contains__(self, item):
        """
        Private method that evaluates if an item belongs to this container.

        :type item: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: bool
        """

        return self.hasMember(item) or self.hasPublishedNode(item)

    def icon(self):
        """
        Returns the container icon.
        If there is no icon then the parent method is used.

        :rtype: QtGui.QIcon
        """

        # Check if icon path exists
        #
        iconPath = os.path.expandvars(self.iconName)

        if os.path.isfile(iconPath):

            return QtGui.QIcon(iconPath)

        else:

            return super(ContainerBaseMixin, self).icon()

    def hasHyperLayout(self):
        """
        Checks if this container has a hyper layout.

        :rtype: bool
        """

        return not self.hyperLayout.isNull()

    def getHyperLayout(self):
        """
        Returns a hyper layout for this container.
        If there is already a hyper layout attached to this container then that node is returned instead!

        :rtype: mpynode.nodetypes.hyperlayoutmixin.HyperLayoutMixin
        """

        # Check for redundancy
        #
        if self.hasHyperLayout():

            return self.pyFactory(self.hyperLayout)

        else:

            hyperLayout = self.pyFactory.createNode('hyperLayout')
            self.hyperLayout = hyperLayout.object()

            return hyperLayout

    def members(self):
        """
        Returns a list of members belonging to this container.

        :rtype: list[mpynode.nodetypes.dependencymixin.DependencyMixin]
        """

        return self.getHyperLayout().members()

    def hasMember(self, member):
        """
        Checks if the supplied dependency node belongs to this container

        :type member: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: bool
        """

        return self.getHyperLayout().hasMember(member.object())

    def addMember(self, member):
        """
        Method used to add a new member to this container.

        :type member: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: bool
        """

        self.getHyperLayout().addMember(member.object())

    def addMembers(self, members):
        """
        Method used to add a list of nodes to this container.

        :type members: list[mpynode.nodetypes.dependencymixin.DependencyMixin]
        :rtype: None
        """

        for member in members:

            self.addMember(member)

    def removeMember(self, member):
        """
        Method used to remove a member from this container.

        :type member: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: None
        """

        # Check if this container has a hyper layout
        #
        return self.getHyperLayout().removeMember(member.object())

    def removeMembers(self, members):
        """
        Method used to remove a list of members from this container.

        :type members: list[mpynode.nodetypes.dependencymixin.DependencyMixin]
        :rtype: None
        """

        for member in members:

            self.removeMember(member)

    def deleteMembers(self):
        """
        Deletes all members connected to the hyper layout.
        This node must be locked before deleting associated members!
        Otherwise Maya will delete any empty transforms following this operation!

        :rtype: None
        """

        # Lock container to prevent Maya from deleting it!
        #
        self.lock()

        # Delete members from hyper layout
        #
        if self.hasHyperLayout():

            hyperLayout = self.getHyperLayout()
            hyperLayout.deleteMembers()
            hyperLayout.delete()

        # Unlock container so we can edit it again
        #
        self.unlock()

    def publishNode(self, node, index=None, alias=None):
        """
        Publishes the supplied node to this container.

        :type node: mpynode.nodetypes.dependencymixin.DependencyMixin
        :type index: int
        :type alias: str
        :rtype: bool
        """

        # Check for redundancy
        #
        if self.hasPublishedNode(node):

            return False

        # Check if index is valid
        #
        if index is None:

            index = self.getNextAvailablePublishedNodeIndex()

        # Get published node info
        #
        publishedNodeInfo = self.getPublishedNodeInfo(index)
        publishedNodeInfo.setPublishedNode(node.object())

        # Check if node has an alias
        #
        if alias is not None:

            publishedNodeInfo.setAlias(alias)

        return True

    def publishNodes(self, nodes):
        """
        Publishes a sequence of nodes to this container.
        This method expects a sequence of tuples with alias and node pairs or a dictionary!

        :type nodes: Union[list, dict]
        :rtype None
        """

        # Check sequence type
        #
        if isinstance(nodes, list):

            # Iterate through nodes
            #
            for (index, node) in enumerate(nodes):

                # Check value type
                #
                if isinstance(node, tuple):

                    self.publishNode(node[1], index=index, alias=node[0])

                else:

                    self.publishNode(node, index=index)

        elif isinstance(nodes, dict):

            # Iterate through nodes
            #
            for (index, (alias, node)) in enumerate(nodes.items()):

                self.publishNode(node, index=index, alias=alias)

        else:

            raise TypeError('publishNodes() expects a sequences (%s given)!' % type(nodes).__name__)

    def unpublishNode(self, node):
        """
        Un-publishes the supplied node from this container.

        :type node: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: None
        """

        # Check if node has been published
        #
        index = self.getPublishedNodeIndex(node)

        if index is None:

            return

        # Get published node info and reset
        #
        publishedNodeInfo = self.getPublishedNodeInfo(index)
        publishedNodeInfo.resetPublishedNode()

    def getPublishedNode(self, index):
        """
        Returns a published node based on the supplied index.

        :type index: Union[int, str]
        :rtype: mpynode.nodetypes.transformmixin.TransformMixin
        """

        # Get published node info
        #
        publishedNodeInfo = self.getPublishedNodeInfo(index)

        if publishedNodeInfo.hasPublishedNode():

            return self.pyFactory(publishedNodeInfo.publishedNode())

        else:

            return None

    def getPublishedJoint(self, index):
        """
        Returns a published joint based on the supplied index.

        :type index: Union[int, str]
        :rtype: mpynode.nodetypes.jointmixin.JointMixin
        """

        # Get published node info
        #
        publishedNodeInfo = self.getPublishedNodeInfo(index)

        if publishedNodeInfo.hasPublishedNode():

            return self.pyFactory(publishedNodeInfo.publishedJoint())

        else:

            return None

    def publishedNodes(self):
        """
        Returns a list of published nodes from this container.

        :rtype: list[mpynode.nodetypes.transformmixin.TransformMixin]
        """

        return list(self.iterPublishedNodes())

    def publishedNodeCount(self):
        """
        Returns the number of published nodes.

        :rtype: int
        """

        return len(self.publishedNodes())

    def hasPublishedNodes(self):
        """
        Checks if this container has any published nodes.

        :rtype: bool
        """

        return self.publishedNodeCount() > 0

    def hasPublishedNode(self, publishedNode):
        """
        Checks if the given node has already been published to this container

        :type publishedNode: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: bool
        """

        return self.getPublishedNodeIndex(publishedNode) is not None

    def isPublishedNode(self):
        """
        Checks if this transform has been published.

        :rtype: bool
        """

        return self.getAssociatedContainer() is not None

    def getPublishedAlias(self):
        """
        Returns the published alias for this transform node.
        If this transform has not been published then an empty string is returned!

        :rtype: str
        """

        # Check if transform has been published
        #
        if self.isPublishedNode():

            return self.getAssociatedContainer().getPublishedNodeAlias(self)

        else:

            return ''

    def getAssociatedContainer(self):
        """
        Returns the container node this transform is associated with.
        If this transform has not been published then none is returned!

        :rtype: mpynode.nodetypes.containermixin.ContainerMixin
        """

        # Iterate through destination plugs
        #
        plug = self.findPlug('message')
        destinations = plug.destinations()

        for destination in destinations:

            # Check if connected plug is a container
            #
            node = destination.node()
            partialName = destination.partialName(useLongNames=True)

            if node.hasFn(om.MFn.kContainerBase) and partialName == 'publishedNode':

                return self.pyFactory(node)

            else:

                continue

        return None

    def getPublishedNodeIndex(self, publishedNode):
        """
        Returns the logical plug index for the supplied dependency node.
        If the node has not been published then none will be returned!

        :type publishedNode: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: int
        """

        # Find connect message plug
        #
        plug = self.findConnectedMessage(publishedNode.object(), self.attribute('publishedNode'))

        if plug is not None:

            return plug.parent().logicalIndex()

        else:

            return None

    def getPublishedNodeAlias(self, publishedNode):
        """
        Returns the plug alias for the supplied dependency node.
        If the node has not been published then an empty string will be returned!

        :type publishedNode: mpynode.nodetypes.dependencymixin.DependencyMixin
        :rtype: str
        """

        # Find connect message plug
        #
        plug = self.findConnectedMessage(publishedNode.object(), self.attribute('publishedNode'))

        if plug is not None:

            return plug.parent().partialName(useAlias=True)

        else:

            return None

    def iterPublishedNodes(self):
        """
        Generator method used to iterate through all of the published nodes.

        :rtype: iter
        """

        # Iterate through published node info
        #
        for publishedNodeInfo in self.iterPublishedNodeInfo(skipEmptyElements=True):

            yield self.pyFactory(publishedNodeInfo.publishedNode())

    def publishedJoints(self):
        """
        Returns a list of published joints from this container.

        :rtype: list[mpynode.nodetypes.jointmixin.JointMixin]
        """

        return list(self.iterPublishedJoints())

    def iterPublishedJoints(self):
        """
        Generator method used to iterate through all of the published joints.

        :rtype: iter
        """

        # Iterate through published node info
        #
        for publishedNodeInfo in self.iterPublishedNodeInfo(skipEmptyElements=True):

            yield self.pyFactory(publishedNodeInfo.publishedJoint())

    def getPublishedNodeInfo(self, index):
        """
        Retrieves a published node info interface for the specified index.

        :type index: Union[int, str]
        :rtype: PublishedNodeInfo
        """

        # Check index type
        #
        if isinstance(index, string_types):

            index = self.findPlug(self.getAliases()[index]).logicalIndex()

        # Return published node info
        #
        return PublishedNodeInfo(self, index=index)

    def iterPublishedNodeInfo(self, skipEmptyElements=False):
        """
        Generator method used to iterate through all of the published node info slots.
        An optional flag can be supplied to ignore empty entries.

        :type skipEmptyElements: bool
        :rtype: iter
        """

        # Iterate through plug elements
        #
        plug = self.findPlug('publishedNodeInfo')
        numElements = plug.numElements()

        for physicalIndex in range(numElements):

            # Get element at physical index
            #
            element = plug.elementByPhysicalIndex(physicalIndex)
            logicalIndex = element.logicalIndex()

            publishedNodeInfo = PublishedNodeInfo(self, index=logicalIndex)

            # Check if node info has published node
            #
            if not publishedNodeInfo.hasPublishedNode() and skipEmptyElements:

                continue

            else:

                yield publishedNodeInfo

    def resetPublishedNodeInfo(self):
        """
        Removes all excess published node info plug indices.

        :rtype: None
        """

        # Check if this container has any published nodes
        #
        if self.hasPublishedNodes():

            return

        # Remove all plug indices
        #
        plug = self.findPlug('publishedNodeInfo')
        indices = plug.getExistingArrayAttributeIndices()

        self.removePlugIndices(plug, indices)

    def getNextAvailablePublishedNodeIndex(self):
        """
        Locates the next available published node slot.

        :rtype: int
        """

        return self.getNextAvailableConnection('publishedNodeInfo', child=self.attribute('publishedNode'))


class PublishedNodeInfo(object):
    """
    Base class used to interface with published nodes.
    """

    __slots__ = ('_container', '_index')

    def __init__(self, container, **kwargs):
        """
        Inherited method called after a new instance has been created.

        :type container: ContainerMixin
        :rtype: None
        """

        # Call parent method
        #
        super(PublishedNodeInfo, self).__init__()

        # Declare class variables
        #
        self._container = container.weakReference()
        self._index = kwargs.get('index', 0)

    @property
    def container(self):
        """
        Getter method used to retrieve the associated container for this published node info.

        :rtype: ConstraintMixin
        """

        return self._container()

    @property
    def index(self):
        """
        Getter method used to retrieve the index for this published node.

        :rtype: int
        """

        return self._index

    def publishedNodeInfoPlug(self):
        """
        Returns the compound plug element for this published node info.

        :rtype: om.MPlug
        """

        return self.container.findPlug('publishedNodeInfo[%s]' % self.index)

    def publishedNodeInfoChildPlug(self, child):
        """
        Returns the child plug for this published node info.

        :type child: str
        :rtype: om.MPlug
        """

        return self.publishedNodeInfoPlug().child(self.container.attribute(child))

    def alias(self):
        """
        Returns the alias name for this published node.

        :rtype: str
        """

        return self.publishedNodeInfoPlug().partialName(useAlias=True)

    def hasAlias(self):
        """
        Checks if this published node info has an alias.

        :rtype: bool
        """

        return len(self.alias()) > 0

    def setAlias(self, alias):
        """
        Method used to change the alias name on the indexed weight attribute.

        :type alias: str
        :rtype: bool
        """

        # Assign new alias to plug
        #
        plug = self.publishedNodeInfoPlug()
        success = self.container.setAlias(alias, plug, replace=True)

        if not success:

            log.warning('Unable to assign {alias} alias to {plugName}!'.format(alias=alias, plugName=plug.info))

        return success

    def hasPublishedNode(self):
        """
        Checks if the dependency node for this published node info is valid.

        :rtype: bool
        """

        return not self.publishedNodeInfoChildPlug('publishedNode').source().isNull

    def publishedNode(self):
        """
        Retrieves the published node object from this node info.

        :rtype: om.MObject
        """

        return self.container.getAttr('publishedNodeInfo[%s].publishedNode' % self.index)

    def setPublishedNode(self, dependNode):
        """
        Updates the published node associated with this node info.

        :type dependNode: om.MObject
        :rtype: None
        """

        self.container.setAttr('publishedNodeInfo[%s].publishedNode' % self.index, dependNode)

    def resetPublishedNode(self):
        """
        Method used to reset the published node back to none.

        :rtype: None
        """

        self.setPublishedNode(om.MObject.kNullObj)

    def hasPublishedJoint(self):
        """
        Checks if the joint for this published node info is valid.

        :rtype: bool
        """

        return not self.publishedNodeInfoChildPlug('publishedJoint').source().isNull

    def publishedJoint(self):
        """
        Retrieves the published joint object from this node info.

        :rtype: om.MObject
        """

        return self.container.getAttr('publishedNodeInfo[%s].publishedJoint' % self.index)

    def setPublishedJoint(self, dependNode):
        """
        Updates the published joint associated with this node info.

        :type dependNode: om.MObject
        :rtype: None
        """

        self.container.setAttr('publishedNodeInfo[%s].publishedJoint' % self.index, dependNode)

    @property
    def publishedNodeType(self):
        """
        Getter method used to retrieve the published node type.
        The published node type indicates which node types can be published to this node info.
        By leaving this blank any node can be connected.

        :rtype: str
        """

        return self.publishedNodeInfoChildPlug('publishedNodeType').asString()

    @publishedNodeType.setter
    def publishedNodeType(self, publishedNodeType):
        """
        Setter method used to updates the node type which can be published to this node info.

        :rtype: str
        """

        self.publishedNodeInfoChildPlug('publishedNodeType').setString(publishedNodeType)

    @property
    def isHierarchicalNode(self):
        """
        Getter method used to retrieve the hierarchical flag for this node info.
        This flag indicates if this node is part of a hierarchy of published nodes.
        By setting this to false the hierarchy will be flatten when black boxed.

        :rtype: bool
        """

        return self.publishedNodeInfoChildPlug('isHierarchicalNode').asBool()

    @isHierarchicalNode.setter
    def isHierarchicalNode(self, isHierarchicalNode):
        """
        Setter method used to update the hierarchy state of this published node.

        :type isHierarchicalNode: bool
        :rtype: None
        """

        self.publishedNodeInfoChildPlug('isHierarchicalNode').setBool(isHierarchicalNode)
