import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from Qt import QtGui
from six import string_types
from dcc.python import stringutils
from dcc.maya.libs import dagutils, attributeutils, plugutils, plugmutators, animutils
from .. import mpyattribute, mpynode
from ..collections import userproperties

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DependencyMixin(mpynode.MPyNode):
    """
    Overload of `MPyNode` that interfaces with dependency graph nodes.
    """

    # region Attributes
    caching = mpyattribute.MPyAttribute('caching')
    frozen = mpyattribute.MPyAttribute('frozen')
    isHistoricallyInteresting = mpyattribute.MPyAttribute('isHistoricallyInteresting')
    nodeState = mpyattribute.MPyAttribute('nodeState')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kDependencyNode

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance is created.

        :type obj: Union[str, om.MObject]
        :rtype: None
        """

        # Call parent method
        #
        super(DependencyMixin, self).__init__(obj, **kwargs)

        # Declare private variables
        #
        self._userProperties = userproperties.UserProperties(self.object())

    def __repr__(self):
        """
        Private method that returns a string representation of this node.

        :rtype: str
        """

        return f'<{self.typeName}:{self.name()} @ {self.handle().hashCode()}>'

    def __str__(self):
        """
        Private method that stringifies this node.

        :rtype: str
        """

        return self.name(includeNamespace=True)

    def __getitem__(self, key):
        """
        Private method used to an indexed plug.

        :type key: Union[str, om.MObject]
        :rtype: om.MPlug
        """

        return self.findPlug(key)

    def __setitem__(self, key, value):
        """
        Private method used to update an indexed plug.

        :type key: Union[str, om.MObject]
        :type value: Any
        :rtype: None
        """

        plugmutators.setValue(self.findPlug(key), value)

    def __reduce__(self):
        """
        The cPickle module uses the __reduce__() method to instruct it on how to simplify the class into a string.

        :return: Tuple containing the class and constructor arguments.
        :rtype: tuple[type, tuple[str]]
        """

        return self.__class__, (self.name(),)
    # endregion

    # region Properties
    @property
    def typeName(self):
        """
        Getter method used to retrieve the type name for this node.

        :rtype: str
        """

        return self.functionSet().typeName

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

    @property
    def userProperties(self):
        """
        Getter method that returns the user properties.

        :rtype: userproperties.UserProperties
        """

        return self._userProperties

    @userProperties.setter
    def userProperties(self, userProperties):
        """
        Setter method that updates the user properties.

        :type userProperties: dict
        :rtype: None
        """

        self._userProperties.update(userProperties)

    @property
    def userPropertyBuffer(self):
        """
        Getter method that returns the user property buffer.

        :rtype: str
        """

        return self._userProperties.buffer()

    @userPropertyBuffer.setter
    def userPropertyBuffer(self, userPropertyBuffer):
        """
        Setter method that updates the user property buffer.

        :type userPropertyBuffer: str
        :rtype: None
        """

        self._userProperties.setBuffer(userPropertyBuffer)
    # endregion

    # region Methods
    def name(self, includeNamespace=False):
        """
        Returns the name of this node.

        :type includeNamespace: bool
        :rtype: str
        """

        absoluteName = self.functionSet().name()
        name = dagutils.stripAll(absoluteName)

        if includeNamespace:

            return '{namespace}:{name}'.format(namespace=self.namespace(), name=name)

        else:

            return name

    def setName(self, newName):
        """
        Updates the name of this object.
        If any name conflicts arise then the original node name will be returned.

        :type newName: str
        :rtype: str
        """

        return self.functionSet().setName(newName)

    def namespace(self):
        """
        Returns the namespace this node belongs to.

        :rtype: str
        """

        return self.functionSet().namespace

    def icon(self):
        """
        Returns the icon used for this node type.

        :rtype: QtGui.QIcon
        """

        if self.isFromPlugin:

            return QtGui.QIcon(':/{typeName}.png'.format(typeName=self.typeName))

        else:

            return QtGui.QIcon(':/{typeName}.svg'.format(typeName=self.typeName))

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

        return self.scene(list(dagutils.iterNodes(apiType=om.MFn.kTime))[0])

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

    def getAssociatedReferenceNode(self):
        """
        Returns the reference node associated with this node.
        If this node is not referenced the none will be returned!

        :rtype: mpynode.MPyNode
        """

        # Check if node is referenced
        #
        if self.isFromReferencedFile:

            return self.scene(dagutils.getAssociatedReferenceNode(self.object()))

        else:

            return None

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

    def uuid(self, asString=False):
        """
        Returns the UUID associated with this node.
        Please note that these values are unique to the reference they belong to and NOT the scene as a whole.

        :type asString: bool
        :rtype: Union[om.MUuid, str]
        """

        uuid = self.functionSet().uuid()

        if asString:

            return uuid.asString()

        else:

            return uuid

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
        This method piggybacks off of the maya command.

        :rtype: iter
        """

        attributes = mc.listAttr(self.name(includeNamespace=True), **kwargs)

        if not stringutils.isNullOrEmpty(attributes):

            return iter(map(self.attribute, attributes))

        else:

            return iter([])

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
        This method accepts data types as attribute type flags for your convenience.

        :key longName: str
        :key attributeType: str
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
            if not self.hasAttr(attribute):

                log.warning('Cannot locate attribute: %s' % attribute)
                return

            # Remove attribute from node
            #
            self.removeAttr(self.attribute(attribute))

        elif isinstance(attribute, om.MObject):

            # Check if this is a valid attribute
            #
            if not attribute.hasFn(om.MFn.kAttribute):

                raise TypeError('removeAttr() expects a valid attribute (%s given)!' % attribute.apiTypeStr)

            # Remove attribute from node
            #
            self.functionSet().removeAttribute(attribute)

        else:

            raise TypeError('removeAttr() expects either a str or MObject (%s given)!' % type(attribute).__name__)

    def getAttr(self, plug, convertUnits=True):
        """
        Returns the value from the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type convertUnits: bool
        :rtype: Any
        """

        # Check plug type
        #
        if isinstance(plug, om.MPlug):

            return plugmutators.getValue(plug, convertUnits=convertUnits)

        elif isinstance(plug, string_types):

            plug = self.findPlug(plug)
            return self.getAttr(plug, convertUnits=convertUnits)

        elif isinstance(plug, om.MObject):

            plug = om.MPlug(self.object(), plug)
            return self.getAttr(plug, convertUnits=convertUnits)

        else:

            raise TypeError('getAttr() expects a plug (%s given)!' % type(plug).__name__)

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

            return plugmutators.setValue(plug, value, force=force)

        elif isinstance(plug, string_types):

            plug = self.findPlug(plug)
            return self.setAttr(plug, value, force=force)

        elif isinstance(plug, om.MObject):

            plug = om.MPlug(self.object(), plug)
            return self.setAttr(plug, value, force=force)

        else:

            raise TypeError('setAttr() expects a plug (%s given)!' % type(plug).__name__)

    def resetAttr(self, plug, force=False):
        """
        Updates the value for the supplied plug back to its default value.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type force: bool
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, om.MPlug):

            return plugmutators.resetValue(plug, force=force)

        elif isinstance(plug, string_types):

            plug = self.findPlug(plug)
            return self.resetAttr(plug, force=force)

        elif isinstance(plug, om.MObject):

            plug = om.MPlug(self.object(), plug)
            return self.resetAttr(plug, force=force)

        else:

            raise TypeError('resetAttr() expects a plug (%s given)!' % type(plug).__name__)

    def hideAttr(self, *attributes):
        """
        Hides an attribute that belongs to this node.

        :type attributes: Union[str, List[str]]
        :rtype: None
        """

        # Iterate through attributes
        #
        for attribute in attributes:

            # Verify attribute is valid
            #
            attribute = self.attribute(attribute)

            if not attribute.hasFn(om.MFn.kAttribute):

                continue

            # Modify attribute
            #
            fnAttribute = om.MFnAttribute(attribute)
            fnAttribute.hidden = True
            fnAttribute.channelBox = False

    def showAttr(self, *attributes):
        """
        Un-hides an attribute that belongs to this node.

        :type attributes: Union[str, List[str], om.MObject, om.MObjectArray]
        :rtype: None
        """

        # Iterate through attributes
        #
        for attribute in attributes:

            # Verify attribute is valid
            #
            attribute = self.attribute(attribute)

            if not attribute.hasFn(om.MFn.kAttribute):

                continue

            # Modify attribute
            #
            fnAttribute = om.MFnAttribute(attribute)
            fnAttribute.hidden = False
            fnAttribute.channelBox = True

    def keyAttr(self, plug, value, frame=None):
        """
        Keys an attribute with the supplied value at the specified time.
        If no time is specified then the current time is used instead!

        :type plug: om.MPlug
        :type value: Any
        :type frame: Union[int, None]
        :rtype: mpy.nodetypes.animcurvemixin.AnimCurveMixin
        """

        # Ensure plug is keyed
        #
        plug = self.findPlug(plug)
        animCurve = animutils.ensureKeyed(plug)

        if animCurve is None:

            return

        # Modify anim curve
        #
        frame = frame if frame is not None else self.scene.time

        animCurve = self.scene(animCurve)
        animCurve.setValueAtFrame(value, frame)

        return animCurve

    def clearKeys(self):
        """
        Removes all animation curves connected to this node.

        :rtype: None
        """

        # Iterate through plugs
        #
        for plug in self.iterPlugs(channelBox=True):

            # Check if plug is animated
            #
            if not plugutils.isAnimated(plug):

                continue

            # Delete anim curve
            #
            animCurve = plug.source().node()
            dagutils.deleteNode(animCurve)

    def getAliases(self):
        """
        Returns a dictionary of aliases from this node.
        The keys represent the aliases whereas the values represent the original name.

        :rtype: Dict[str, str]
        """

        return plugutils.getAliases(self.object())

    def setAlias(self, plug, alias):
        """
        Updates the alias for the supplied plug.

        :type plug: om.MPlug
        :type alias: str
        :rtype: bool
        """

        return plugutils.setAlias(plug, alias)

    def removeAlias(self, plug):
        """
        Removes the alias from the supplied plug.

        :type plug: Union[str, om.MPlug]
        :rtype: bool
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Remove any aliases from plug
        #
        return plugutils.removeAlias(plug)

    def attribute(self, name):
        """
        Returns an attribute based on the supplied name.
        Unlike the api method, this implementation supports redundancy checks for plugs.

        :type name: Union[str, om.MObject, om.MPlug]
        :rtype: om.MObject
        """

        # Redundancy check
        #
        if isinstance(name, om.MObject):

            return name

        # Evaluate argument type
        #
        if isinstance(name, string_types):

            return self.functionSet().attribute(name)

        elif isinstance(name, om.MPlug):

            return name.attribute()

        else:

            raise TypeError('findAttribute() expects either a str or MPlug (%s given)!' % type(name).__name__)

    def findPlug(self, name):
        """
        Returns a plug based on the supplied plug path.
        Unlike the api method, this implementation supports both compound and indexed plugs.

        :type name: Union[str, om.MObject, om.MPlug]
        :rtype: om.MPlug
        """

        # Redundancy check
        #
        if isinstance(name, om.MPlug):

            return name

        # Evaluate argument type
        #
        if isinstance(name, string_types):

            return plugutils.findPlug(self.object(), name)

        elif isinstance(name, om.MObject):

            return om.MPlug(self.object(), name)

        else:

            raise TypeError('findPlug() expects either a str or MObject (%s given)!' % type(name).__name__)

    def iterPlugs(self, channelBox=False):
        """
        Returns a generator that yields plugs from this node.

        :type channelBox: bool
        :rtype: Iterator[om.MPlug]
        """

        if channelBox:

            return plugutils.iterChannelBoxPlugs(self.object())

        else:

            return plugutils.iterTopLevelPlugs(self.object())

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

                    self.connectPlugs(source.child(i), destination.child(i), force=force)

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
        By default, these arguments are set to true for maximum breakage!

        :type plug: Union[str, om.MPlug]
        :type source: bool
        :type destination: bool
        :type recursive: bool
        :rtype: None
        """

        # Check plug type
        #
        if isinstance(plug, string_types):

            plug = self.findPlug(plug)

        # Break connections on plug
        #
        plugutils.breakConnections(plug, source=source, destination=destination, recursive=recursive)

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

    def dependsOn(self, apiType=om.MFn.kDependencyNode, typeName=''):
        """
        Returns a list of nodes that this object is dependent on.

        :type apiType: int
        :type typeName: str
        :rtype: List[DependencyMixin]
        """

        return [self.scene(dependency) for dependency in dagutils.iterDependencies(self.object(), apiType, typeName=typeName, direction=om.MItDependencyGraph.kUpstream)]

    def dependents(self, apiType=om.MFn.kDependencyNode, typeName=''):
        """
        Returns a list of nodes that are dependent on this object.

        :type apiType: int
        :type typeName: str
        :return: List[DependencyMixin]
        """

        return [self.scene(dependency) for dependency in dagutils.iterDependencies(self.object(), apiType, typeName=typeName, direction=om.MItDependencyGraph.kDownstream)]
    # endregion
