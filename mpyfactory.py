import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.abstract import proxyfactory
from dcc.maya.libs import dagutils
from . import mpynode, nodetypes, plugintypes

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyFactory(proxyfactory.ProxyFactory):
    """
    Overload of AbstractFactory used to manage python interfaces for Maya scene nodes.
    """

    __slots__ = ('__plugins__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(MPyFactory, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self.__plugins__ = dict(self.iterPackages(plugintypes, classAttr='__plugin__'))

    def __call__(self, dependNode):
        """
        Private method called whenever this instance is evoked.
        This method will act as a quick initializer for dependency nodes.

        :type dependNode: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
        :rtype: mpynode.MPyNode
        """

        return mpynode.MPyNode(dependNode)

    def packages(self):
        """
        Returns a list of packages to be searched for factory classes.

        :rtype: list[module]
        """

        return [nodetypes]

    def classAttr(self):
        """
        Returns the attribute name to be used to organize the class dictionary.

        :rtype: str
        """

        return '__apitype__'

    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: class
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

        else:

            return self.getMixin(dependNode)

    def isPlugin(self, dependNode):
        """
        Checks if the supplied node is derived from a plugin.
        By default the function set will always return a string.
        So we run a path validation to test.

        :type dependNode: om.MObject
        :rtype: bool
        """

        return os.path.exists(om.MFnDependencyNode(dependNode).pluginName)

    def getPlugin(self, dependNode):
        """
        Returns a mixin class that is compatible with the given dependency node.

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
        :rtype: iter
        """

        # Check for root namespace
        #
        if len(namespace) == 0:

            namespace = ':'

        # Try and collect namespace objects
        #
        try:

            # Iterate through objects in namespace
            #
            for dependNode in om.MNamespace.getNamespaceObjects(namespace):

                yield mpynode.MPyNode(dependNode)

        except RuntimeError as exception:

            log.error(exception)
            return

    def getNodesByNamespace(self, namespace):
        """
        Returns a list of nodes belonging to the supplied namespace.

        :type namespace: str
        :rtype: list[mpynode.MPyNode]
        """

        return list(self.iterNodesByNamespace(namespace))

    def iterNodesByApiType(self, apiType):
        """
        Returns a generator that iterates over nodes based on the given api type.

        :type apiType: int
        :rtype: iter
        """

        # Iterate through dependency nodes
        #
        for dependNode in dagutils.iterNodes(apiType=apiType):

            yield mpynode.MPyNode(dependNode)

    def getNodesByApiType(self, apiType):
        """
        Returns a list of nodes based on the given api type.

        :type apiType: int
        :rtype: list[mpynode.MPyNode]
        """

        return list(self.iterNodesByApiType(apiType=apiType))

    def iterNodesByTypeName(self, typeName):
        """
        Returns a generator that yields nodes based on the supplied type name.

        :type typeName: str
        :rtype: iter
        """

        # Iterate through dependency nodes
        #
        for nodeName in mc.ls(type=typeName, long=True):

            yield mpynode.MPyNode(nodeName)

    def getNodesByTypeName(self, typeName):
        """
        Returns a list of nodes based on the given type name.

        :type typeName: str
        :rtype: list[mpynode.MPyNode]
        """

        return list(self.iterNodesByTypeName(typeName))

    def createNode(self, typeName, name='', parent=None, skipSelect=True):
        """
        Creates a new scene node and immediately wraps it in a MPyNode interface.
        Any dictionaries supplied as a name will be passed to namingutils for concatenation.

        :type typeName: str
        :type name: str
        :type parent: Union[str, om.MObject, om.MDagPath, mpynode.MPyNode]
        :type skipSelect: bool
        :rtype: mpynode.MPyNode
        """

        # Check if name is valid
        #
        if isinstance(name, string_types) and len(name) == 0:

            name = '{typeName}1'.format(typeName=typeName)

        # Check if a non-string parent was supplied
        #
        if isinstance(parent, mpynode.MPyNode):

            parent = parent.fullPathName()

        elif isinstance(parent, (om.MObject, om.MDagPath)):

            parent = om.MFnDagNode(parent).fullPathName()

        else:

            pass

        # Try and create node
        #
        try:

            partialPathName = mc.createNode(typeName, name=name, parent=parent, skipSelect=skipSelect)
            return mpynode.MPyNode(partialPathName)

        except RuntimeError as exception:

            log.warning(exception)
            return None

    def createReference(self, filePath, namespace=''):
        """
        Returns a new reference node using the supplied file.

        :type filePath: str
        :type namespace: str
        :rtype: mpynode.MPyNode
        """

        # Check if file exists
        #
        if not os.path.exists(filePath):

            raise TypeError('createReference() expects a valid file!')

        # Create new reference
        #
        nodes = mc.file(filePath, reference=True, namespace=namespace, returnNewNodes=True)
        numNodes = len(nodes)

        if numNodes > 0:

            return mpynode.MPyNode(nodes[0]).getAssociatedReferenceNode()

        else:

            nodeName = '{namespace}RN'.format(namespace=namespace)
            return mpynode.MPyNode(nodeName)  # TODO: This needs improving!

    @classmethod
    def selection(cls, apiType=om.MFn.kDependencyNode):
        """
        Returns the active selection.
        An optional api type can be supplied to narrow down the selection.

        :type apiType: int
        :rtype: list[mpynode.MPyNode]
        """

        return list(cls.iterSelection(apiType=apiType))

    @staticmethod
    def iterSelection(apiType=om.MFn.kDependencyNode):
        """
        Returns a generator that can iterate through the active selection.
        An optional api type can be supplied to narrow down the selection.

        :type apiType: int
        :rtype: list[mpynode.MPyNode]
        """

        for dependNode in dagutils.iterActiveSelection(apiType=apiType):

            yield mpynode.MPyNode(dependNode)

    def getAttributeTemplate(self, name):
        """
        Returns an attribute template from the supplied name.
        No error checking is performed to test if this file actually exists!

        :rtype: str
        """

        filename = '{name}.json'.format(name=name)
        return os.path.join(os.path.dirname(__file__), 'templates', filename)

    def getShapeTemplate(self, name):
        """
        Returns a shape template from the supplied name.
        No error checking is performed to test if this file actually exists!

        :rtype: str
        """

        filename = '{name}.json'.format(name=name)
        return os.path.join(os.path.dirname(__file__), 'shapes', filename)


def getPyFactory():
    """
    Returns the PyFactory instance.
    Reduces the amount of extra code I have to write...

    :rtype: MPyFactory
    """

    return MPyFactory.getInstance()


def getPyFactoryReference():
    """
    Returns the PyFactory instance as a weak reference.
    Again, reduces the amount of extra code I have to write...

    :rtype: weakref.ref
    """

    return getPyFactory().weakReference()
