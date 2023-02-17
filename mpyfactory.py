import inspect
import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.abstract import proxyfactory
from dcc.python import stringutils, importutils
from dcc.naming import namingutils
from dcc.maya.libs import dagutils, sceneutils
from . import mpynode, nodetypes, plugintypes
from .collections import fileproperties

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyFactory(proxyfactory.ProxyFactory):
    """
    Overload of ProxyFactory that manages python interfaces for Maya scene nodes.
    """

    # region Dunderscores
    __slots__ = ('__plugins__', '__extensions__', '__properties__')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Check if instance has already been initialized
        #
        if not self.hasInstance():

            self.__plugins__ = dict(self.iterPackages(plugintypes, classAttr='__plugin__'))
            self.__extensions__ = {}
            self.__properties__ = fileproperties.FileProperties()

        # Call parent method
        #
        super(MPyFactory, self).__init__(*args, **kwargs)

    def __call__(self, dependNode):
        """
        Private method called whenever this instance is evoked.
        This method will act as a quick initializer for dependency nodes.

        :type dependNode: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
        :rtype: mpynode.MPyNode
        """

        return mpynode.MPyNode(dependNode)
    # endregion

    # region Properties
    @ property
    def name(self):
        """
        Getter method that returns the current scene's name.

        :rtype: str
        """

        return sceneutils.currentFilename(includeExtension=False)

    @property
    def filename(self):
        """
        Getter method that returns the current scene's file name.

        :rtype: str
        """

        return sceneutils.currentFilename()

    @property
    def filePath(self):
        """
        Getter method that returns the current scene's file path.

        :rtype: str
        """

        return sceneutils.currentFilePath()

    @property
    def directory(self):
        """
        Getter method that returns the current scene's directory.

        :rtype: str
        """

        return sceneutils.currentDirectory()

    @property
    def projectPath(self):
        """
        Getter method that returns the current project directory.

        :rtype: str
        """

        return sceneutils.currentProjectDirectory()

    @property
    def namespace(self):
        """
        Getter method that returns the current namespace.

        :rtype: str
        """

        return sceneutils.currentNamespace()

    @property
    def time(self):
        """
        Getter method that returns the current time.

        :rtype: int
        """

        return sceneutils.getTime()

    @time.setter
    def time(self, time):
        """
        Setter method that updates the current time.

        :rtype: int
        """

        sceneutils.setTime(time)

    @property
    def startTime(self):
        """
        Getter method that returns the current start-time.

        :rtype: int
        """

        return sceneutils.getStartTime()

    @startTime.setter
    def startTime(self, time):
        """
        Setter method that updates the current start-time.

        :rtype: int
        """

        sceneutils.setStartTime(time)

    @property
    def endTime(self):
        """
        Getter method that returns the current end-time.

        :rtype: int
        """

        return sceneutils.getEndTime()

    @endTime.setter
    def endTime(self, time):
        """
        Setter method that updates the current end-time.

        :rtype: int
        """

        sceneutils.setEndTime(time)

    @property
    def animationRange(self):
        """
        Getter method that returns the current animation range.

        :rtype: Tuple[int, int]
        """

        return sceneutils.getAnimationRange()

    @animationRange.setter
    def animationRange(self, animationRange):
        """
        Setter method that updates the current animation range.

        :type animationRange: Tuple[int, int]
        :rtype: None
        """

        sceneutils.setAnimationRange(*animationRange)

    @property
    def autoKey(self):
        """
        Getter method that returns the auto-key state.

        :rtype: bool
        """

        return sceneutils.autoKey()

    @autoKey.setter
    def autoKey(self, state):
        """
        Setter method that updates the auto-key state.

        :type state: bool
        :rtype: None
        """

        sceneutils.setAutoKey(state)

    @property
    def properties(self):
        """
        Getter method that returns the scene properties.

        :rtype: fileproperties.FileProperties
        """

        return self.__properties__
    # endregion

    # region Methods
    def packages(self):
        """
        Returns a list of packages to be searched for factory classes.

        :rtype: List[module]
        """

        return [nodetypes]

    def classAttr(self):
        """
        Returns the attribute name to be used to organize the class dictionary.

        :rtype: str
        """

        return '__api_type__'

    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: Callable
        """

        return mpynode.MPyNode

    def getClass(self, dependNode):
        """
        Returns a class constructor based on the supplied key.

        :type dependNode: om.MObject
        :rtype: class
        """

        # Check if this is an extension node
        #
        if self.isPlugin(dependNode):

            return self.getPlugin(dependNode)

        elif self.isExtension(dependNode):

            return self.getExtensionMixin(dependNode)

        else:

            return self.getMixin(dependNode)

    def isPlugin(self, dependNode):
        """
        Evaluates if the supplied node is derived from a plugin.
        By default, the function set will always return a string.
        So we run a path validation to test it.

        :type dependNode: om.MObject
        :rtype: bool
        """

        return os.path.exists(om.MFnDependencyNode(dependNode).pluginName)

    def getPlugin(self, dependNode):
        """
        Returns a plugin class that is compatible with the given dependency node.

        :type dependNode: om.MObject
        :rtype: class
        """

        # Check if plugin name correlates with any keys
        #
        fnDependNode = om.MFnDependencyNode(dependNode)
        cls = self.__plugins__.get(fnDependNode.typeName, None)

        if cls is not None:

            return cls

        else:

            return self.getMixin(dependNode)

    def isExtension(self, dependNode):
        """
        Evaluates if the supplied node uses an extension interface.
        This consists of a python class name and module path.

        :type dependNode: om.MObject
        :rtype: bool
        """

        fnDependNode = om.MFnDependencyNode(dependNode)
        return fnDependNode.hasAttribute('__class__') and fnDependNode.hasAttribute('__module__')

    def createExtensionClass(self, mixinClass, extensionClass):
        """
        Combines the supplied mixin and extension classes into a new class.

        :type mixinClass: class
        :type extensionClass: class
        :rtype: class
        """

        # Evaluate supplied classes
        #
        if not inspect.isclass(extensionClass) or not inspect.isclass(mixinClass):

            raise TypeError('createExtensionClass() expects a mixin and extension class!')

        # Check if class already exists
        #
        fullTypeName = '{mixinName}+{extensionName}'.format(mixinName=mixinClass.__name__, extensionName=extensionClass.__name__)
        cls = self.__extensions__.get(fullTypeName, None)

        if cls is None:

            cls = type(fullTypeName, (mixinClass, extensionClass), {})
            self.__extensions__[fullTypeName] = cls

        return cls

    def getExtensionMixin(self, dependNode):
        """
        Returns an extension class that is compatible with the given dependency node.

        :type dependNode: om.MObject
        :rtype: class
        """

        # Check if this node uses an extension interface
        #
        if not self.isExtension(dependNode):

            raise TypeError('getExtension() cannot locate extension attributes!')

        # Get class name and module path
        #
        fnDependNode = om.MFnDependencyNode(dependNode)

        className = fnDependNode.findPlug('__class__', False).asString()
        modulePath = fnDependNode.findPlug('__module__', False).asString()

        if stringutils.isNullOrEmpty(className) or stringutils.isNullOrEmpty(modulePath):

            raise TypeError('getExtension() expects a valid class and module!')

        # Find associated interfaces
        #
        extensionClass = importutils.findClass(className, modulePath)
        mixinClass = self.getPlugin(dependNode)

        return self.createExtensionClass(mixinClass, extensionClass)

    def getMixin(self, dependNode):
        """
        Returns a mixin class that is compatible with the given dependency node.

        :type dependNode: om.MObject
        :rtype: class
        """

        # Check if api type correlates with any keys
        #
        apiType = dependNode.apiType()
        cls = super(MPyFactory, self).getClass(apiType)

        if cls is not None:

            return cls

        # Collect all compatible mixin types
        # Be sure to exclude any plugins since they throw off the inheritance depth
        #
        classes = [x for x in self.__classes__.values() if x.isCompatible(dependNode) and not hasattr(x, '__plugin__')]
        numClasses = len(classes)

        if numClasses == 0:

            raise TypeError('getClass() expects a valid node type (%s given)!' % dependNode.apiTypeStr)

        elif numClasses == 1:

            cls = classes[0]

        else:

            # Find the best class using inheritance depth
            #
            depths = [x.inheritanceDepth() for x in classes]
            maxDepth = max(depths)

            index = depths.index(maxDepth)
            cls = classes[index]

        # Update classes for future lookups
        #
        self.__classes__[apiType] = cls
        return cls

    def doesNodeExist(self, nodeName):
        """
        Evaluates if a node with the supplied name exists.

        :type nodeName: str
        :rtype: bool
        """

        return mc.objExists(nodeName)

    def getNodeByName(self, name):
        """
        Returns a node interface based on the given node name.

        :type name: str
        :rtype: mpynode.MPyNode
        """

        try:

            dependNode = dagutils.getMObjectByName(name)
            return mpynode.MPyNode(dependNode)

        except TypeError as exception:

            log.warning(exception)
            return None

    def getNodeByHashCode(self, hashCode):
        """
        Returns a node interface via hash code.
        Remember that hash codes do not persist between sessions!

        :rtype: mpynode.MPyNode
        """

        return mpynode.MPyNode.__instances__.get(hashCode, None)

    def getNodeByUuid(self, uuid, referenceNode=None):
        """
        Retrieves a node interface from the given UUID.
        An optional reference node can be supplied to narrow down the results in case of duplicates.

        :type uuid: Union[str, om.MUuid]
        :type referenceNode: mpynode.MPyNode
        :rtype: mpynode.MPyNode
        """

        # Check value type
        #
        if isinstance(uuid, string_types):

            uuid = om.MUuid(uuid)

        # Check if reference node was supplied
        #
        if referenceNode is not None:

            # Perform safe lookup using reference node
            #
            return referenceNode.getNodeByUuid(uuid)

        else:

            # Get all objects from uuid
            #
            found = dagutils.getMObjectByMUuid(uuid)

            if isinstance(found, om.MObject):

                return mpynode.MPyNode(found)

            elif isinstance(found, (list, tuple)):

                return [mpynode.MPyNode(x) for x in found]

            else:

                return None

    def iterNodesByNamespace(self, namespace):
        """
        Generator method used to iterate through the objects belong to the supplied namespace.
        If you want to return the root namespace objects be sure to supply a semicolon!

        :type namespace: str
        :rtype: Iterator[mpynode.MPyNode]
        """

        # Check for root namespace
        #
        if stringutils.isNullOrEmpty(namespace):

            namespace = ':'

        # Check if namespace exists
        #
        if om.MNamespace.namespaceExists(namespace):

            # Iterate through objects in namespace
            #
            for dependNode in om.MNamespace.getNamespaceObjects(namespace):

                yield mpynode.MPyNode(dependNode)

        else:

            return iter([])

    def getNodesByNamespace(self, namespace):
        """
        Returns a list of nodes belonging to the supplied namespace.

        :type namespace: str
        :rtype: List[mpynode.MPyNode]
        """

        return list(self.iterNodesByNamespace(namespace))

    def iterNodesByApiType(self, apiType):
        """
        Returns a generator that iterates over nodes based on the given api type.

        :type apiType: int
        :rtype: Iterator[mpynode.MPyNode]
        """

        return map(mpynode.MPyNode, dagutils.iterNodes(apiType=apiType))

    def getNodesByApiType(self, apiType):
        """
        Returns a list of nodes based on the given api type.

        :type apiType: int
        :rtype: List[mpynode.MPyNode]
        """

        return list(self.iterNodesByApiType(apiType=apiType))

    def iterNodesByTypeName(self, typeName):
        """
        Returns a generator that yields nodes based on the supplied type name.

        :type typeName: str
        :rtype: Iterator[mpynode.MPyNode]
        """

        return map(mpynode.MPyNode, dagutils.iterNodes(typeName=typeName))

    def getNodesByTypeName(self, typeName):
        """
        Returns a list of nodes based on the given type name.

        :type typeName: str
        :rtype: List[mpynode.MPyNode]
        """

        return list(self.iterNodesByTypeName(typeName))

    def iterNodesByPattern(self, *patterns, apiType=om.MFn.kDependencyNode):
        """
        Returns a generator that yields nodes based on the supplied name patterns.

        :type patterns: Union[str, Tuple[str]]
        :type apiType: int
        :rtype: Iterator[mpynode.MPyNode]
        """

        return map(mpynode.MPyNode, dagutils.iterNodesByPattern(*patterns, apiType=apiType))

    def getNodesByPattern(self, *patterns, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes based on the supplied name patterns.

        :type patterns: Union[str, Tuple[str]]
        :type apiType: int
        :rtype: List[mpynode.MPyNode]
        """

        return list(self.iterNodesByPattern(*patterns, apiType=apiType))

    def iterExtensions(self):
        """
        Returns a generator that yields nodes with extensions.

        :rtype: Iterator[mpynodeextension.MPyNodeExtension]
        """

        nodeNames = mc.ls('*.__class__', long=True, objectsOnly=True)

        if not stringutils.isNullOrEmpty(nodeNames):

            yield from map(self, nodeNames)

        else:

            return iter([])

    def getExtensions(self):
        """
        Returns a list of nodes with extensions.

        :rtype: List[mpynodeextension.MPyNodeExtension]
        """

        return list(self.iterExtensions())

    def iterExtensionsByTypeName(self, typeName):
        """
        Returns a generator that yields nodes with the specified extension name.

        :rtype: Iterator[mpynodeextension.MPyNodeExtension]
        """

        for extension in self.iterExtensions():

            typeNames = [base.__name__ for base in extension.__class__.iterBases()]

            if typeName in typeNames:

                yield extension

            else:

                continue

    def getExtensionsByTypeName(self, typeName):
        """
        Returns a list of nodes with the specified extension name.

        :rtype: List[mpynodeextension.MPyNodeExtension]
        """

        return list(self.iterExtensionsByTypeName(typeName))

    def iterSelection(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a generator that can iterate through the active selection.
        An optional api type can be supplied to narrow down the selection.

        :type apiType: int
        :rtype: Iterator[mpynode.MPyNode]
        """

        for dependNode in dagutils.iterActiveSelection(apiType=apiType):

            yield mpynode.MPyNode(dependNode)

    def selection(self, apiType=om.MFn.kDependencyNode):
        """
        Returns the active selection.
        An optional api type can be supplied to narrow down the selection.

        :type apiType: int
        :rtype: List[mpynode.MPyNode]
        """

        return list(self.iterSelection(apiType=apiType))

    def setSelection(self, selection):
        """
        Updates the active selection.

        :type selection: Union[om.MSelectionList, List[om.MObject]]
        :rtype: None
        """

        # Evaluate selection list
        #
        if isinstance(selection, om.MSelectionList):

            om.MGlobal.setActiveSelectionList(selection)

        elif isinstance(selection, list):

            selection = dagutils.createSelectionList(selection)
            self.setSelection(selection)

        else:

            raise TypeError('setSelection() expects a selection list (%s given)!' % type(selection).__name__)

    def getShapeTemplate(self, name):
        """
        Returns a shape template from the supplied name.
        No error checking is performed to test if this file actually exists!

        :rtype: str
        """

        directory = os.path.dirname(os.path.abspath(__file__))
        filename = '{name}.json'.format(name=name)

        return os.path.join(directory, 'shapes', filename)

    def createNode(self, typeName, name='', parent=None, skipSelect=True, **kwargs):
        """
        Creates a new scene node and wraps it in a MPyNode interface.

        :type typeName: str
        :type name: Union[str, dict]
        :type parent: Union[str, om.MObject, om.MDagPath, mpynode.MPyNode]
        :type skipSelect: bool
        :rtype: mpynode.MPyNode
        """

        # Check if name requires concatenating
        #
        if isinstance(name, dict):

            name = namingutils.concatenateName(**name)

        # Check if a valid parent was supplied
        #
        node = None

        if parent is None:

            # Create dependency node
            #
            fnDependNode = om.MFnDependencyNode()
            dependNode = fnDependNode.create(typeName)

            # Check if a valid name was supplied
            #
            if isinstance(name, string_types) and not stringutils.isNullOrEmpty(name):

                fnDependNode.setName(name)

            node = mpynode.MPyNode(dependNode)

        else:

            # Ensure parent type is compatible
            #
            if isinstance(parent, mpynode.MPyNode):

                parent = parent.object()

            else:

                parent = dagutils.getMObject(parent)

            # Create dag node
            #
            fnDagNode = om.MFnDagNode()
            dagNode = fnDagNode.create(typeName, parent=parent)

            # Check if a valid name was supplied
            #
            if isinstance(name, string_types) and not stringutils.isNullOrEmpty(name):

                fnDagNode.setName(name)

            node = mpynode.MPyNode(dagNode)

        # Check if node should be selected
        #
        if not skipSelect:

            node.select(replace=True)

        return node

    def createDisplayLayer(self, name, includeSelected=False, includeDescendants=False):
        """
        Creates a new display layer and wraps it in an MPyNode interface.

        :type name: str
        :type includeSelected: bool
        :type includeDescendants: bool
        :rtype: mpynode.MPyNode
        """

        # Check if a null-name was supplied
        #
        if stringutils.isNullOrEmpty(name):

            name = 'layer1'

        # Try and display layer
        #
        try:

            nodeName = mc.createDisplayLayer(name=name, empty=(not includeSelected), noRecurse=(not includeDescendants))
            return mpynode.MPyNode(nodeName)

        except RuntimeError as exception:

            log.error(exception)
            return None

    def createShadingNode(self, typeName, name='', parent=None, **kwargs):
        """
        Creates a new shading node and wraps it in a MPyNode interface.

        :type typeName: str
        :type name: str
        :type parent: Union[str, om.MObject, om.MDagPath, mpynode.MPyNode]
        :key asLight: bool
        :key asPostProcess: bool
        :key asRendering: bool
        :key asShader: bool
        :key asTexture: bool
        :key asUtility: bool
        :key isColorManaged: bool
        :key shared: bool
        :key skipSelect: bool
        :rtype: mpynode.MPyNode
        """

        # Check if a null-name was supplied
        #
        if stringutils.isNullOrEmpty(name):

            name = '{typeName}1'.format(typeName=typeName)

        # Check if a non-string parent was supplied
        #
        if isinstance(parent, mpynode.MPyNode):

            parent = parent.fullPathName()

        elif isinstance(parent, (om.MObject, om.MDagPath)):

            parent = om.MFnDagNode(parent).fullPathName()

        else:

            pass

        # Try and create shader node
        #
        try:

            shaderName = mc.shadingNode(typeName, name=name, parent=parent, **kwargs)
            return mpynode.MPyNode(shaderName)

        except RuntimeError as exception:

            log.error(exception)
            return None

    def createShader(self, typeName, name=''):
        """
        Creates a new shader and wraps the node and engine in a MPyNode interface.

        :type typeName: str
        :type name: str
        :rtype: Tuple[mpynode.MPyNode, mpynode.MPyNode]
        """

        # Check if a null-name was supplied
        #
        shaderName, shadingGroupName = None, None

        if stringutils.isNullOrEmpty(name):

            shaderName = '{typeName}1'.format(typeName=typeName)
            shadingGroupName = '{shaderName}SG'.format(shaderName=shaderName)

        else:

            shaderName = name
            shadingGroupName = '{shaderName}SG'.format(shaderName=shaderName)

        # Try and create shader components
        #
        try:

            shaderName = mc.shadingNode(typeName, name=shaderName, asShader=True)
            shadingGroupName = mc.sets(name=shadingGroupName, empty=True, renderable=True, noSurfaceShader=True)

            shader, shadingGroup = mpynode.MPyNode(shaderName), mpynode.MPyNode(shadingGroupName)
            shader.connectPlugs('outColor', shadingGroup['surfaceShader'])

            return shader, shadingGroup

        except RuntimeError as exception:

            log.error(exception)
            return None, None

    def createReference(self, filePath, namespace=''):
        """
        Creates a new reference node using the supplied file.

        :type filePath: str
        :type namespace: str
        :rtype: mpynode.MPyNode
        """

        # Check if file exists
        #
        absolutePath = os.path.normpath(os.path.expandvars(filePath))

        if not os.path.exists(absolutePath):

            raise TypeError('createReference() cannot locate file: %s' % filePath)

        # Create new reference
        #
        nodes = mc.file(filePath, reference=True, namespace=namespace, returnNewNodes=True)
        numNodes = len(nodes)

        if numNodes > 0:

            return mpynode.MPyNode(nodes[0]).getAssociatedReferenceNode()

        else:

            nodeName = '{namespace}RN'.format(namespace=namespace)
            return mpynode.MPyNode(nodeName)  # TODO: This needs improving!
    # endregion
