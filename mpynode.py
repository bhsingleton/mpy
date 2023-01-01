from maya.api import OpenMaya as om
from abc import ABCMeta
from six import with_metaclass
from dcc.maya.libs import dagutils
from dcc.decorators.classproperty import classproperty
from .abstract import mobjectwrapper

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyNode(with_metaclass(ABCMeta, mobjectwrapper.MObjectWrapper)):
    """
    Overload of MObjectWrapper used as the base class for all Maya node interfaces.
    This class supports a range of constructor arguments that are outlined under the __accepts__ attribute.
    All derived classes should overload the __apitype__ attribute, that way they can be registered by MPyFactory!
    """

    # region Dunderscores
    __accepts__ = (str, om.MObjectHandle, om.MObject, om.MDagPath)
    __apitype__ = om.MFn.kBase
    __pyfactory__ = None
    __instances__ = {}

    def __new__(cls, obj, **kwargs):
        """
        Private method called before a new instance is created.
        This method is responsible for moderating the instantiation of valid dependency nodes.

        :type obj: Union[str, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: MPyNode
        """

        # Inspect object type
        #
        if isinstance(obj, cls.__accepts__):  # Default

            # Evaluate class type
            # If MPyNode is being directly instantiated then we must replace the base class!
            #
            if cls is MPyNode:

                handle = dagutils.getMObjectHandle(obj)
                return cls.getInstance(handle)

            else:

                return super(MPyNode, cls).__new__(cls)

        elif isinstance(obj, MPyNode):  # Redundancy check

            return obj

        elif isinstance(obj, int):  # Hash lookup

            return cls.__instances__.get(obj, None)

        else:

            raise TypeError('MPyNode() expects %s (%s given)!' % (cls.__accepts__, type(obj).__name__))
    # endregion

    # region Properties
    @classproperty
    def nodeManager(cls):
        """
        Returns the node factory class.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: mpy.mpyfactory.MPyFactory
        """

        # Check if factory exists
        #
        if cls.__pyfactory__ is None:

            from . import mpyfactory
            cls.__pyfactory__ = mpyfactory.MPyFactory.getInstance(asWeakReference=True)

        return cls.__pyfactory__()
    # endregion

    # region Methods
    @classmethod
    def isCompatible(cls, dependNode):
        """
        Evaluates whether the supplied object is compatible with this class.

        :type dependNode: om.MObject
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(dependNode, om.MObject):

            raise TypeError('isCompatible() expects an MObject (%s given)!' % type(dependNode).__name__)

        # Check api type
        #
        apiType = cls.__apitype__

        if isinstance(apiType, int):

            return dependNode.hasFn(apiType)

        elif isinstance(apiType, (list, tuple)):

            return any([dependNode.hasFn(x) for x in apiType])

        else:

            raise TypeError('isCompatible() expects a valid type constant (%s given)!' % type(apiType).__name__)

    @classmethod
    def getInstance(cls, handle):
        """
        Returns an instance associated with the given object handle.

        :type handle: om.MObjectHandle
        :rtype: MPyNode
        """

        # Check if object handle is alive
        #
        if not handle.isAlive():

            return None

        # Check if value has already been initialized
        #
        dependNode = handle.object()
        hashCode = handle.hashCode()

        instance = cls.__instances__.get(hashCode, None)

        if instance is not None:

            # Check if instance is still alive
            # If not then we need to reinitialize it!
            #
            if not instance.isAlive():

                del cls.__instances__[hashCode]
                return cls.getInstance(handle)

            else:

                return instance

        else:

            # Create new instance
            # Be sure to replace the base class with the correct type!
            #
            instance = super(MPyNode, cls).__new__(cls)
            instance.__class__ = cls.nodeManager.getClass(dependNode)

            cls.__instances__[hashCode] = instance
            return instance

    @classmethod
    def create(cls, typeName, name='', parent=None, skipSelect=True):
        """
        Returns a new dependency node of the specified type.

        :type typeName: str
        :type name: Union[str, Dict[str, Any]]
        :type parent: Union[str, om.MObject, om.MDagPath, MPyNode]
        :type skipSelect: bool
        :rtype: MPyNode
        """

        return cls.nodeManager.createNode(typeName, name=name, parent=parent)

    def hasExtension(self):
        """
        Evaluates if this instance has an extension.

        :rtype: bool
        """

        return self.nodeManager.isExtension(self.object())

    def addExtension(self, extensionClass):
        """
        Adds the supplied extension to this node.

        :type extensionClass: class
        :rtype: None
        """

        # Redundancy check
        #
        if self.hasExtension():

            return

        # Reinitialize instance
        #
        self.__class__ = self.nodeManager.createExtensionClass(self.__class__, extensionClass)
        self.__init__(self.object())

    def removeExtension(self):
        """
        Removes any extensions from this node.

        :rtype: None
        """

        # Redundancy check
        #
        if not self.hasExtension():

            return

        # Remove extension related attributes
        #
        plug = self.findPlug('metadata')

        self.breakConnections(plug, recursive=True)
        self.removeAttr(plug.attribute())

        # Update class
        #
        self.__class__ = self.nodeManager.getClass(self.object())

    def delete(self):
        """
        Removes this instance from the scene file.
        Be careful calling any instance method after deleting this node.
        Any references to a null pointer will result in a crash!

        :rtype: None
        """

        dagutils.deleteNode(self.object())
    # endregion
