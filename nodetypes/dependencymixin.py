import maya.cmds as mc
import maya.api.OpenMaya as om
import re
import os

from PySide2 import QtGui

from .. import mpyattribute, mpynode
from ..utilities import attributeutils, plugutils, dagutils
from ..utilities.pyutils import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DependencyMixin(mpynode.MPyNode):
    """
    Overload of PyNode used to interface with dependency graph nodes.
    """

    __apitype__ = om.MFn.kDependencyNode
    __plugparser__ = re.compile(r'([a-zA-Z]+)\[?([0-9]*)\]?')

    caching = mpyattribute.MPyAttribute('caching')
    frozen = mpyattribute.MPyAttribute('frozen')
    isHistoricallyInteresting = mpyattribute.MPyAttribute('isHistoricallyInteresting')
    nodeState = mpyattribute.MPyAttribute('nodeState')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(DependencyMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        """
        Private method used to an indexed plug.

        :type key: str
        :rtype: om.MPlug
        """

        return self.findPlug(key)

    def __setitem__(self, key, value):
        """
        Private method used to update an indexed plug.

        :type key: str
        :type value: Any
        :rtype: None
        """

        plugutils.setValue(self.findPlug(key), value)

    def __reduce__(self):
        """
        The cPickle module uses the __reduce__() method to instruct it on how to simplify the class into a string.

        :return: Tuple containing the class and constructor arguments.
        :rtype: tuple[type, tuple[str]]
        """

        return self.__class__, (self.name(),)

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return self.functionSet().name()

    def setName(self, newName):
        """
        Updates the name of this object.
        If any name conflicts arise then the original node name will be returned.

        :type newName: str
        :rtype: str
        """

        return self.functionSet().setName(newName)

    def displayName(self):
        """
        Returns a name suitable for user interfaces.
        This includes no namespace or pipes.

        :rtype: str
        """

        return dagutils.stripAll(self.name())

    def namespace(self):
        """
        Returns the namespace this node belongs to.

        :rtype: str
        """

        return self.functionSet().namespace

    @property
    def typeName(self):
        """
        Getter method used to retrieve the type name for this node.

        :rtype: str
        """

        return self.functionSet().typeName

    def icon(self):
        """
        Returns the icon used for this node type.

        :rtype: QtGui.QIcon
        """

        if self.isFromPlugin:

            return QtGui.QIcon(f':/{self.typeName}.png')

        else:

            return QtGui.QIcon(f':/{self.typeName}.svg')

    def select(self, replace=False):
        """
        Method used to select this instance.

        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        selection = om.MSelectionList()

        if not replace:

            selection = om.MGlobal.getActiveSelectionList()

        # Reset active selection
        #
        selection.add(self.object())
        om.MGlobal.setActiveSelectionList(selection)

    def deselect(self):
        """
        Method used to deselect this instance.

        :rtype: None
        """

        # Get active selection
        #
        selection = om.MGlobal.getActiveSelectionList()
        item = self.object()

        if selection.hasItem(item):

            selection.remove(item)

        # Reset active selection
        #
        om.MGlobal.setActiveSelectionList(selection)

    def isSelected(self):
        """
        Method used to check if this object is currently selected.

        :rtype: bool
        """

        return om.MGlobal.getActiveSelectionList().hasItem(self.object())

    def time(self):
        """
        Returns the global time node.

        :rtype: DependencyMixin
        """

        return self.pyFactory(list(dagutils.iterNodes(apiType=om.MFn.kTime))[0])

    def currentTime(self):
        """
        Returns the current time.

        :rtype: om.MTime
        """

        return self.time().getAttr('outTime')

    def setCurrentTime(self, currentTime):
        """
        Updates the current time.

        :type currentTime: Union[int, float, om.MTime]
        :rtype: None
        """

        self.time().setAttr('outTime', currentTime)

    @property
    def isFromPlugin(self):
        """
        Getter method used to determine if this node is derived from a plugin file.

        :rtype: bool
        """

        return os.path.exists(self.functionSet().pluginName)

    @property
    def isFromReferencedFile(self):
        """
        Getter method used to determine if this node is derived from a referenced file.

        :rtype: bool
        """

        return self.functionSet().isFromReferencedFile

    def getAssociatedReferenceNode(self):
        """
        Returns the reference node associated with this node.
        If this node is not referenced the none will be returned!

        :rtype: mpynode.MPyNode
        """

        # Check if node is referenced
        #
        if self.isFromReferencedFile:

            return self.pyFactory(dagutils.getAssociatedReferenceNode(self.object()))

        else:

            return None

    def rename(self, name):
        """
        Method used to rename this instance to the supplied name.
        No error checking is performed so please inspect your values before supplying them to this method!

        :type name: str
        :rtype: str
        """

        return self.functionSet().setName(name)

    def lock(self):
        """
        Method used to lock this node and prevent user changes.

        :rtype: None
        """

        self.functionSet().isLocked = True

    def unlock(self):
        """
        Method used to unlock this node and allow the user to edit the node.

        :rtype: None
        """

        self.functionSet().isLocked = False

    @property
    def isLocked(self):
        """
        Property method used to determine if this node is locked.

        :rtype: bool
        """

        return self.functionSet().isLocked

    @isLocked.setter
    def isLocked(self, isLocked):
        """
        Setter method used to change the lock state on this node.

        :type isLocked: bool
        :rtype: bool
        """

        self.functionSet().isLocked = isLocked

    def uuid(self):
        """
        Returns the UUID associated with this node.
        Please note that these values are unique to the reference they belong to and NOT the scene as a whole.

        :rtype: om.MUuid
        """

        return om.MUuid(self.functionSet().uuid())

    def setUuid(self, uuid):
        """
        Changes the unique identification value associated with this node.

        :type uuid: str
        :rtype: None
        """

        return self.functionSet().setUuid(uuid)

    def iterAttr(self, **kwargs):
        """
        Returns a generator that can iterate over attributes derived from this node.
        This method piggy backs off of the maya command.

        :rtype: iter
        """

        for name in mc.listAttr(self.absoluteName(), **kwargs):

            yield self.attribute(name)

    def listAttr(self, **kwargs):
        """
        Returns a list of attributes derived from this node.

        :rtype: list[om.MObject]
        """

        return list(self.iterAttr(**kwargs))

    def hasAttr(self, attribute):
        """
        Checks if this node has the supplied attribute.

        :type attribute: str
        :rtype: bool
        """

        return self.functionSet().hasAttribute(attribute)

    def addAttr(self, *args, **kwargs):
        """
        Adds a user attribute to this node.
        No need for the data type flag since attributeutils compensates for that.

        :keyword longName: str
        :keyword attributeType: str
        :rtype: om.MObject
        """

        return attributeutils.addAttribute(self.object(), **kwargs)

    def removeAttr(self, attribute):
        """
        Removes an attribute from this node.

        :type attribute: Union[str, om.MObject]
        :rtype: None
        """

        # Check value type
        #
        if isinstance(attribute, string_types):

            # Check if node has attribute
            #
            if self.hasAttr(attribute):

                return self.removeAttr(self.attribute(attribute))

            else:

                return

        elif isinstance(attribute, om.MObject):

            # Check if this is a valid attribute
            #
            if attribute.hasFn(om.MFn.kAttribute):

                self.functionSet().removeAttribute(attribute)

            else:

                return

        else:

            raise TypeError('removeAttr() expects either a str or MObject (%s given)!' % type(attribute).__name__)

    def getAttr(self, plug):
        """
        Returns the value from the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :rtype: object
        """

        # Check plug type
        #
        if isinstance(plug, om.MPlug):

            return plugutils.getValue(plug)

        elif isinstance(plug, string_types):

            return self.getAttr(self.findPlug(plug))

        elif isinstance(plug, om.MObject):

            return self.getAttr(om.MPlug(self.object(), plug))

        else:

            raise TypeError(f'getAttr() expects a plug ({type(plug).__name__} given)!')

    def getAttrType(self, attribute):
        """
        Returns the api type for the supplied attribute.

        :type attribute: str
        :rtype: int
        """

        return self.attribute(attribute).apiType()

    def getAttrTypeName(self, attribute):
        """
        Returns the api typename for the supplied attribute.

        :type attribute: str
        :rtype: str
        """

        return self.attribute(attribute).apiTypeStr

    def setAttr(self, plug, value, force=False):
        """
        Updates the value for the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type value: object
        :type force: bool
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, om.MPlug):

            return plugutils.setValue(plug, value, force=force)

        elif isinstance(plug, string_types):

            return self.setAttr(self.findPlug(plug), value, force=force)

        elif isinstance(plug, om.MObject):

            return self.setAttr(om.MPlug(self.object(), plug), value, force=force)

        else:

            raise TypeError(f'setAttr() expects a plug ({type(plug).__name__} given)!')

    def getAliases(self):
        """
        Returns a dictionary of all of the attribute aliases belonging to this node.
        The keys represent the alias name and the values represent the original name.

        :rtype: dict[str, str]
        """

        return plugutils.getAliases(self.object())

    def setAlias(self, alias, plug, replace=False):
        """
        Updates the alias for the supplied plug.

        :type alias: str
        :type plug: om.MPlug
        :type replace: bool
        :rtype: bool
        """

        # Check if alias should be replaced
        #
        if replace:

            self.removeAlias(self.plugsAlias(plug))

        # Create new plug alias
        #
        return self.functionSet().setAlias(alias, plug.partialName(useLongNames=True), plug, add=True)

    def setAliases(self, plug, aliases):
        """
        Updates the values for the supplied array plug while assigning aliases to each element.

        :type plug: Union[str, om.MPlug]
        :type aliases: dict[str, object]
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        return plugutils.setAliases(plug, aliases)

    def removePlugAlias(self, plug):
        """
        Removes the alias from the supplied plug.

        :type plug: Union[str, om.MPlug]
        :rtype: bool
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Check if plug has alias before removing
        #
        alias = self.plugsAlias(plug)
        hasAlias = len(alias) > 0

        if hasAlias:

            return self.functionSet().setAlias(alias, plug.partialName(useLongNames=True), plug, add=False)

        else:

            return False

    def removeAlias(self, alias):
        """
        Removes the alias from this dependency node.

        :type alias: str
        :rtype: bool
        """

        # Check for redundancy
        #
        numChars = len(alias)

        if numChars == 0:

            return

        # Check if alias is in use
        #
        aliases = self.getAliases()
        plugName = aliases.get(alias, None)

        if plugName is not None:

            return self.removePlugAlias(plugName)

        else:

            return False

    def hideAttr(self, attribute):
        """
        Hides an attribute that belongs to this node.

        :type attribute: Union[str, om.MObject]
        :rtype: None
        """

        # Check attribute type
        #
        if isinstance(attribute, string_types):

            attribute = self.attribute(attribute)

        # Verify attribute is valid
        #
        if not attribute.hasFn(om.MFn.kAttribute):

            return

        # Modify attribute
        #
        fnAttribute = om.MFnAttribute(attribute)
        fnAttribute.hidden = True
        fnAttribute.channelBox = False

    def hideAttrs(self, attributes):
        """
        Hides a list of attributes that belong to this attribute.

        :type attributes: list
        :rtype: None
        """

        # Iterate through attributes
        #
        for attribute in attributes:

            self.hideAttr(attribute)

    def showAttr(self, attribute):
        """
        Un-hides an attribute that belongs to this node.

        :type attribute: Union[str, om.MObject]
        :rtype: None
        """

        # Check attribute type
        #
        if isinstance(attribute, string_types):

            attribute = self.attribute(attribute)

        # Verify attribute is valid
        #
        if not attribute.hasFn(om.MFn.kAttribute):

            return

        # Modify attribute
        #
        fnAttribute = om.MFnAttribute(attribute)
        fnAttribute.hidden = False
        fnAttribute.channelBox = True

    def showAttrs(self, attributes):
        """
        Un-hides a list of attributes that belong to this attribute.

        :type attributes: list[str]
        :rtype: None
        """

        # Iterate through attributes
        #
        for attribute in attributes:

            self.showAttr(attribute)

    def keyAttr(self, attribute):
        """
        Keys an attribute that belongs to this node.

        :type attribute: Union[str, om.MObject]
        :rtype: None
        """

        pass

    def keyAttrs(self, attributes):
        """
        Keys a list of attributes that belongs to this node.

        :type attributes: Union[str, om.MObject]
        :rtype: None
        """

        pass

    def findConnectedMessage(self, dependNode, attribute):
        """
        Locates the connected destination plug for the given dependency node.

        :type dependNode: om.MObject
        :type attribute: Union[str, om.MObject]
        :rtype: om.MPlug
        """

        # Check attribute type
        #
        if isinstance(attribute, string_types):

            attribute = self.attribute(attribute)

        # Find connected message
        #
        return plugutils.findConnectedMessage(dependNode, attribute)

    def findPlug(self, name):
        """
        Method used to find a plug based on the given string path.
        Unlike the api method, this implementation supports both compound and indexed plugs.

        :type name: str
        :rtype: om.MPlug
        """

        return plugutils.findPlug(self.object(), name)

    def connectPlugs(self, source, destination, force=False):
        """
        Method used to connect two plugs.
        If a string is supplied then the plug lookup will be performed relative to this node.

        :type source: Union[str, om.MPlug]
        :type destination: Union[str, om.MPlug]
        :type force: bool
        :rtype: None
        """

        # Check source plug type
        #
        if isinstance(source, string_types):

            source = self.findPlug(source)

        # Check source plug type
        #
        if isinstance(destination, string_types):

            destination = self.findPlug(destination)

        # Check if these are compound plugs
        #
        if source.isCompound and destination.isCompound:

            # Check if child counts are identical
            #
            if source.numChildren() == destination.numChildren():

                # Connect child plugs
                #
                for i in range(source.numChildren()):

                    self.connectPlugs(source.child(i), destination.child(i))

            else:

                plugutils.connectPlugs(source, destination, force=force)

        else:

            plugutils.connectPlugs(source, destination, force=force)

    def disconnectPlugs(self, source, destination):
        """
        Method used to disconnect two plugs.
        If a string is supplied then the plug lookup will be performed relative to this node.

        :type source: Union[str, om.MPlug]
        :type destination: Union[str, om.MPlug]
        :rtype: None
        """

        # Check source plug type
        #
        if isinstance(source, string_types):

            source = self.findPlug(source)

        # Check source plug type
        #
        if isinstance(destination, string_types):

            destination = self.findPlug(destination)

        # Disconnect plugs
        #
        plugutils.disconnectPlugs(source, destination)

    def breakConnections(self, plug, source=True, destination=True, recursive=False):
        """
        Method used to break connections to the supplied plug.
        Optional keyword arguments can be supplied to control the side the disconnect takes place.
        By default these arguments are set to true for maximum breakage!

        :type plug: Union[str, om.MPlug]
        :type source: bool
        :type destination: bool
        :type recursive:bool
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Break connections on plug
        #
        plugutils.breakConnections(plug, source=source, destination=destination, recursive=recursive)

    def getNextAvailableConnection(self, plug, child=om.MObject.kNullObj):
        """
        Finds the next available plug element index.
        If there are no gaps then the last element will be returned.

        :type plug: Union[str, om.MPlug]
        :type child: om.MObject
        :rtype: int
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Get next available plug element
        #
        return plugutils.getNextAvailableConnection(plug, child=child)

    def removePlugIndices(self, plug, indices):
        """
        Removes a list of indices from the supplied array plug.

        :type plug: Union[str, om.MPlug]
        :type indices: list[int]
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Remove plug instances
        #
        plugutils.removeMultiInstances(plug, indices)

    def dependsOn(self, apiType=om.MFn.kDependencyNode):
        """
        Returns nodes that this instance is dependent on.

        :rtype: list[DependencyMixin]
        """

        return [self.pyFactory(x) for x in dagutils.iterDependencies(self.object(), apiType, direction=om.MItDependencyGraph.kUpstream)]

    def dependents(self, apiType=om.MFn.kDependencyNode):
        """
        Returns nodes that are dependent on this instance.

        :return: list[DependencyMixin]
        """

        return [self.pyFactory(x) for x in dagutils.iterDependencies(self.object(), apiType, direction=om.MItDependencyGraph.kDownstream)]
