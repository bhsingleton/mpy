import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from Qt import QtGui
from dcc.python import stringutils
from dcc.naming import namingutils
from dcc.maya.libs import dagutils, attributeutils, plugutils, plugmutators, animutils
from dcc.maya.collections import userproperties
from .. import mpyattribute, mpynode, mpycontext

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

        return dagutils.renameNode(self.object(), newName)

    def namespace(self):
        """
        Returns the namespace this node belongs to.

        :rtype: str
        """

        return self.functionSet().namespace

    def setNamespace(self, namespace):
        """
        Updates the namespace this node belongs to.

        :type namespace: str
        :rtype: None
        """

        self.setName(f'{namespace}:{self.name()}')

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

        if self.isSelected():

            selection.remove(self.object())

        # Reset active selection
        #
        om.MGlobal.setActiveSelectionList(selection)

    def isSelected(self):
        """
        Method used to check if this object is currently selected.

        :rtype: bool
        """

        return om.MGlobal.getActiveSelectionList().hasItem(self.object())

    def lock(self):
        """
        Method used to lock this node and prevent user changes.

        :rtype: None
        """

        self.isLocked = True

    def unlock(self):
        """
        Method used to unlock this node and allow the user to edit the node.

        :rtype: None
        """

        self.isLocked = False

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

        :type uuid: Union[om.MUuid, str]
        :rtype: None
        """

        return self.functionSet().setUuid(uuid)

    def getAssociatedReferenceNode(self):
        """
        Returns the reference node associated with this node.
        If this node is not referenced the none will be returned!

        :rtype: Union[mpy.builtins.referencemixin.ReferenceMixin, None]
        """

        # Check if node is referenced
        #
        if self.isFromReferencedFile:

            return self.scene(dagutils.getAssociatedReferenceNode(self.object()))

        else:

            return None

    def getOppositeNode(self):
        """
        Finds the node opposite to this one.
        If no opposite is found then this node is returned instead!

        :rtype: mpy.builtins.transformmixin.TransformMixin
        """

        # Check if mirror node is defined
        # If not, then mirror the name of this node
        #
        name = self.userProperties.get('mirrorNode', self.name())
        mirrorName = namingutils.mirrorName(name)

        absoluteName = f'{self.namespace()}:{mirrorName}'

        # Check if opposite node exists
        #
        if mc.objExists(absoluteName):

            return self.scene(absoluteName)

        else:

            return self

    def iterAttr(self, **kwargs):
        """
        Returns a generator that can iterate over attributes derived from this node.
        This method uses Maya's `listAttr` command since it performs faster than the alternative API methods?

        :rtype: Iterator[om.MObject]
        """

        attributes = mc.listAttr(self.name(includeNamespace=True), **kwargs)

        if not stringutils.isNullOrEmpty(attributes):

            return iter(map(self.attribute, attributes))

        else:

            return iter([])

    def listAttr(self, **kwargs):
        """
        Returns a list of attributes derived from this node.

        :rtype: List[om.MObject]
        """

        return list(self.iterAttr(**kwargs))

    def hasAttr(self, attribute):
        """
        Checks if this node has the supplied attribute.

        :type attribute: Union[str, om.MObject, om.MPlug]
        :rtype: bool
        """

        if isinstance(attribute, string_types):

            return self.functionSet().hasAttribute(attribute)

        elif isinstance(attribute, om.MObject):

            functionSet = self.functionSet()
            attributes = [functionSet.attribute(i) for i in range(functionSet.attributeCount())]

            return attribute in attributes

        elif isinstance(attribute, om.MPlug):

            return self.hasAttr(attribute.attribute())

        else:

            return False

    def addAttr(self, *args, **kwargs):
        """
        Adds a user attribute to this node.
        This method accepts data types as attribute type flags for your convenience.

        :key longName: str
        :key attributeType: str
        :rtype: om.MObject
        """

        return attributeutils.addAttribute(self.object(), **kwargs)

    def addProxyAttr(self, name, plug):
        """
        Adds a proxy attribute to the supplied plug.

        :type name: str
        :type plug: om.MPlug
        :rtype: om.MObject
        """

        mc.addAttr(self.name(includeNamespace=True), longName=name, proxy=plug.info)
        return self.attribute(name)

    def addDivider(self, title):
        """
        Adds a divider attribute to this node.

        :type title: str
        :rtype: None
        """

        # Add attribute
        #
        dividers = [attr for attr in self.iterAttr(userDefined=True) if om.MFnAttribute(attr).name.startswith('div')]
        numDividers = len(dividers)

        attribute = self.addAttr(longName=f'div{numDividers}', niceName='//', attributeType='enum', fields={title: 0}, channelBox=True)

        # Lock associated plug
        #
        plug = om.MPlug(self.object(), attribute)
        plug.isLocked = True

    def removeAttr(self, attribute):
        """
        Removes an attribute from this node.

        :type attribute: Union[str, om.MObject, om.MPlug]
        :rtype: None
        """

        attribute = self.attribute(attribute)
        self.functionSet().removeAttribute(attribute)

    def getAttr(self, plug, time=None, convertUnits=True):
        """
        Returns the value from the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type time: Union[int, None]
        :type convertUnits: bool
        :rtype: Any
        """

        plug = self.findPlug(plug)

        with mpycontext.MPyContext(time):

            return plugmutators.getValue(plug, convertUnits=convertUnits)

    def tryGetAttr(self, plug, time=None, convertUnits=True, default=None):
        """
        Returns the value from the supplied plug.
        If no plug exists then the default value is returned instead!

        :type plug: Union[str, om.MObject, om.MPlug]
        :type time: Union[int, None]
        :type convertUnits: bool
        :type default: Any
        :rtype: Any
        """

        if self.hasAttr(plug):

            return self.getAttr(plug, time=time, convertUnits=convertUnits)

        else:

            log.debug(f'Cannot locate "{plug}" from {self.name()} node!')
            return default

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

    def setAttr(self, plug, value, **kwargs):
        """
        Updates the value for the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type value: object
        :key convertUnits: bool
        :key force: bool
        :rtype: None
        """

        plug = self.findPlug(plug)
        plugmutators.setValue(plug, value, **kwargs)

    def trySetAttr(self, plug, value, **kwargs):
        """
        Tries to update the value for the supplied plug.

        :type plug: Union[str, om.MObject, om.MPlug]
        :type value: object
        :key convertUnits: bool
        :key force: bool
        :rtype: bool
        """

        if self.hasAttr(plug):

            self.setAttr(plug, value, **kwargs)
            return True

        else:

            log.debug(f'Cannot locate "{plug}" from {self.name()} node!')
            return False

    def dirtyAttr(self, plug, **kwargs):
        """
        Marks the supplied plug as dirty.

        :type plug: Union[str, om.MObject, om.MPlug]
        :key allPlugs: bool
        :key clean: bool
        :key implicit: bool
        :key list: bool
        :key propagation: bool
        :key showTiming: bool
        :key verbose: bool
        :rtype: None
        """

        plug = self.findPlug(plug)
        mc.dgdirty(plug.info, **kwargs)

    def resetAttr(self, plug, **kwargs):
        """
        Updates the value for the supplied plug back to its default value.

        :type plug: Union[str, om.MObject, om.MPlug]
        :key force: bool
        :rtype: None
        """

        plug = self.findPlug(plug)
        plugmutators.resetValue(plug, **kwargs)

    def hideAttr(self, *plugs, lock=False):
        """
        Hides an attribute that belongs to this node.

        :type plugs: Union[str, List[str], om.MPlug, List[om.MPlug]]
        :type lock: bool
        :rtype: None
        """

        for plug in plugs:

            plug = self.findPlug(plug)

            if plug.isCompound:

                for child in plugutils.iterChildren(plug):

                    child.isKeyable = False
                    child.isChannelBox = False
                    child.isLocked = lock

            else:

                plug.isKeyable = False
                plug.isChannelBox = False
                plug.isLocked = lock

    def showAttr(self, *plugs, keyable=False, unlock=False):
        """
        Un-hides an attribute that belongs to this node.

        :type plugs: Union[str, List[str], om.MPlug, List[om.MPlug]]
        :type keyable: bool
        :type unlock: bool
        :rtype: None
        """

        for plug in plugs:

            plug = self.findPlug(plug)

            if plug.isCompound:

                for child in plugutils.iterChildren(plug):

                    child.isKeyable = keyable
                    child.isChannelBox = True
                    child.isLocked = not unlock

            else:

                plug.isKeyable = keyable
                plug.isChannelBox = True
                plug.isLocked = not unlock

    def lockAttr(self, *plugs):
        """
        Locks an attribute that belongs to this node.

        :type plugs: Union[str, List[str], om.MPlug, List[om.MPlug]]
        :rtype: None
        """

        for plug in plugs:

            plug = self.findPlug(plug)

            if plug.isCompound:

                for child in plugutils.iterChildren(plug):

                    child.isLocked = True

            elif plug.isArray and not plug.isElement:

                for element in plugutils.iterElements(plug):

                    element.isLocked = True

            else:

                plug.isLocked = True

    def unlockAttr(self, *plugs):
        """
        Unlocks an attribute that belongs to this node.

        :type plugs: Union[str, List[str], om.MPlug, List[om.MPlug]]
        :rtype: None
        """

        for plug in plugs:

            plug = self.findPlug(plug)

            if plug.isCompound:

                for child in plugutils.iterChildren(plug):

                    child.isLocked = False

            elif plug.isArray and not plug.isElement:

                for element in plugutils.iterElements(plug):

                    element.isLocked = False

            else:

                plug.isLocked = False

    def keyAttr(self, *args, time=None):
        """
        Keys an attribute at the specified time.
        If no value is supplied then the current value is used instead!
        If no time is specified then the current time is used instead!

        :type args: Union[om.MPlug, Tuple[om.MPlug, Any]]
        :type time: Union[int, float, om.MTime, None]
        :rtype: mpy.builtins.animcurvemixin.AnimCurveMixin
        """

        # Inspect supplied arguments
        #
        plug, value = None, None
        numArgs = len(args)

        if numArgs == 1:

            plug = self.findPlug(args[0])
            value = plugmutators.getValue(plug)

        elif numArgs == 2:

            plug, value = self.findPlug(args[0]), args[1]

        else:

            raise TypeError('keyAttr() expects 1-2 arguments (%s given)!' % numArgs)

        # Check if plug is keyable
        #
        if not plug.isKeyable:

            raise TypeError('keyAttr() expects a keyable plug (%s given)!' % plug.info)

        # Check if a valid time was supplied
        #
        if isinstance(time, om.MTime):

            pass

        elif isinstance(time, (int, float)):

            time = om.MTime(time, unit=om.MTime.uiUnit())

        elif time is None:

            time = om.MTime(self.scene.time, unit=om.MTime.uiUnit())

        else:

            raise TypeError('keyAttr() expects a valid time (%s given)!' % type(time).__name__)

        # Check if value should be updated
        #
        animCurve = self.findAnimCurve(plug, create=True)
        animCurve.setValue(time, value, convertUnits=True)

        return animCurve

    def mirrorAttr(self, plug, pull=False, includeKeys=False, animationRange=None, insertAt=None):
        """
        Mirrors the supplied plug to the opposite node.
        If no node is found opposite to this node then itself is used instead!

        :type plug: om.MPlug
        :type pull: bool
        :type includeKeys: bool
        :type animationRange: Union[Tuple[int, int], None]
        :type insertAt: Union[int, None]
        :rtype: None
        """

        # Check if other node has plug
        #
        otherNode = self.getOppositeNode()
        attributeName = om.MFnAttribute(plug.attribute()).name

        if not otherNode.hasAttr(attributeName):

            return

        # Get mirror flag for plug
        #
        plugName = plug.partialName(useLongNames=True, useFullAttributePath=True)
        otherPlug = otherNode.findPlug(plugName)

        mirrorFlag = 'mirror{name}'.format(name=stringutils.titleize(plugName))
        mirrorEnabled = self.userProperties.get(mirrorFlag, False)

        # Inverse value and update other node
        #
        log.debug('Mirroring "%s" > "%s"' % (plug.info, otherPlug.info))

        if pull:

            # Mirror the other value to this node
            #
            value = otherNode.getAttr(otherPlug)
            value *= -1.0 if mirrorEnabled else 1.0

            self.setAttr(plug, value)

            # Check if keys should be included
            #
            if includeKeys and plugutils.isAnimated(otherPlug):

                otherAnimCurve = self.scene(otherPlug.source().node())
                keys = otherAnimCurve.mirrorKeys(animationRange=animationRange)

                animCurve = self.findAnimCurve(plug, create=True)
                animCurve.replaceKeys(keys, animationRange=animationRange, insertAt=insertAt)

        else:

            # Mirror this value to the other node
            #
            value = self.getAttr(plug)
            value *= -1.0 if mirrorEnabled else 1.0

            otherNode.setAttr(plugName, value)

            # Check if keys should be included
            #
            if includeKeys and plugutils.isAnimated(plug):

                animCurve = self.scene(plug.source().node())
                keys = animCurve.mirrorKeys(animationRange=animationRange)

                otherAnimCurve = otherNode.findAnimCurve(otherPlug, create=True)
                otherAnimCurve.replaceKeys(keys, animationRange=animationRange, insertAt=insertAt)

    def clearKeys(self, **kwargs):
        """
        Removes all keyframes from this node.
        Once all keys from an animation curve are removed the curve is deleted!
        An optional animation range can be specified in case you only want to clear a section of keys.

        :key animationRange: Union[Tuple[int, int], None]
        :key skipUserAttributes: bool
        :rtype: None
        """

        # Iterate through plugs
        #
        animationRange = kwargs.get('animationRange', None)

        for plug in self.iterPlugs(channelBox=True, **kwargs):

            # Check if plug is animated
            #
            if not plugutils.isAnimated(plug):

                continue

            # Check if plug should be skipped
            #
            plugName = plug.partialName(useLongNames=True)

            skipKey = 'skip{plugName}'.format(plugName=stringutils.pascalize(plugName))
            skipAllKey = stringutils.stripCartesian(skipKey)
            skipPlug = kwargs.get(skipKey, kwargs.get(skipAllKey, False))

            if skipPlug:

                continue

            # Clear inputs from animation curve
            #
            animCurve = self.findAnimCurve(plug)
            animCurve.clearKeys(animationRange=animationRange)

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

    def findAnimCurve(self, name, create=False):
        """
        Returns an anim curve associated with the supplied plug path.

        :type name: Union[str, om.MObject, om.MPlug]
        :type create: bool
        :rtype: mpy.builtins.animcurvemixin.AnimCurveMixin
        """

        # Check if plug is animated
        #
        plug = self.findPlug(name)

        if plugutils.isAnimatable(plug):

            return self.scene(animutils.findAnimCurve(plug, create=create))

        else:

            return None

    def iterPlugs(self, **kwargs):
        """
        Returns a generator that yields plugs from this node.

        :key readable: bool
        :key writable: bool
        :key nonDefault: bool
        :key channelBox: bool
        :key affectsWorldSpace: bool
        :key skipUserAttributes: bool
        :rtype: Iterator[om.MPlug]
        """

        channelBox = kwargs.get('channelBox', False)

        if channelBox:

            return plugutils.iterChannelBoxPlugs(self.object(), **kwargs)

        else:

            return plugutils.iterTopLevelPlugs(self.object(), **kwargs)

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
            sourceCount = source.numChildren()
            destinationCount = destination.numChildren()

            if sourceCount == destinationCount:

                # Connect child plugs
                #
                for i in range(sourceCount):

                    self.connectPlugs(source.child(i), destination.child(i), force=force)

            else:

                # Connect plugs
                #
                plugutils.connectPlugs(source, destination, force=force)

        elif not source.isCompound and destination.isCompound:

            # Connect source plug to destination's child plugs
            #
            destinationCount = destination.numChildren()

            for i in range(destinationCount):

                self.connectPlugs(source, destination.child(i), force=force)

        else:

            # Connect plugs
            #
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

        # Check if these are compound plugs
        #
        if source.isCompound and destination.isCompound:

            # Check if child counts are identical
            #
            sourceCount = source.numChildren()
            destinationCount = destination.numChildren()

            if sourceCount == destinationCount:

                # Connect child plugs
                #
                for i in range(sourceCount):

                    self.disconnectPlugs(source.child(i), destination.child(i))

            else:

                # Disconnect plugs
                #
                plugutils.disconnectPlugs(source, destination)

        else:

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

    def findConnectedMessage(self, dependNode, attribute=om.MObject.kNullObj):
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

    def removePlugElements(self, plug, indices):
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

    def dependsOn(self, apiType=om.MFn.kDependencyNode, typeName=None):
        """
        Returns a list of nodes that this object is dependent on.

        :type apiType: int
        :type typeName: Union[str, None]
        :rtype: List[DependencyMixin]
        """

        return list(map(self.scene.__call__, dagutils.iterDependencies(self.object(), apiType, typeName=typeName, direction=om.MItDependencyGraph.kUpstream)))

    def dependents(self, apiType=om.MFn.kDependencyNode, typeName=''):
        """
        Returns a list of nodes that are dependent on this object.

        :type apiType: int
        :type typeName: Union[str, None]
        :return: List[DependencyMixin]
        """

        return list(map(self.scene.__call__, dagutils.iterDependencies(self.object(), apiType, typeName=typeName, direction=om.MItDependencyGraph.kDownstream)))
    # endregion
