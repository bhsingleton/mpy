import maya.cmds as mc
import maya.api.OpenMaya as om

from abc import ABCMeta, abstractmethod

from .decorators import classproperty
from .abstract import mobjectwrapper
from .utilities import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyNode(mobjectwrapper.MObjectWrapper, metaclass=ABCMeta):
    """
    Overload of MObjectWrapper used to return Maya node interfaces.
    """

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
        if isinstance(obj, cls.__accepts__):

            # Inspect class type
            # If PyNode is being directly instantiated then we must replace the base class
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

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance has been created.

        :type obj: Union[str, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: None
        """

        # Call parent method
        #
        super(MPyNode, self).__init__(obj, **kwargs)

    @classproperty
    def pyFactory(cls):
        """
        Returns the node factory class.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: mpynode.mpyfactory.MPyFactory
        """

        # Check if factory exists
        #
        if cls.__pyfactory__ is None:

            from . import mpyfactory
            cls.__pyfactory__ = mpyfactory.getPyFactoryReference()

        return cls.__pyfactory__()

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
            # If not then we need to reinitialize it
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
            instance.__class__ = cls.pyFactory.getClass(dependNode)

            cls.__instances__[hashCode] = instance
            return instance

    def delete(self):
        """
        Removes this instance from the scene file.
        Be careful calling any instance method after deleting this node.
        Any references to a null pointer will result in a crash!

        :rtype: None
        """

        dagutils.deleteNode(self.object())
