import inspect
import weakref

from maya.api import OpenMaya as om
from abc import ABCMeta
from six import with_metaclass, string_types
from dcc.decorators.classproperty import classproperty
from dcc.maya.libs import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MObjectWrapper(with_metaclass(ABCMeta, object)):
    """
    Abstract base class used as a low-level wrapper for Maya scene objects.
    A lot of the architecture in this class is designed around dynamically looking up compatible function sets.
    If this class detects an unknown attribute it will attempt to resolve it through the function set.
    """

    __slots__ = ('__weakref__', '__handle__', '__functionset__')
    __functionsets__ = {}

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance has been created.

        :type obj: Union[str, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: None
        """

        # Check if this class has already been initialized
        #
        if self.isInitialized():

            return

        # Declare class variable
        #
        self.__handle__ = dagutils.getMObjectHandle(obj)
        self.__functionset__ = self.findCompatibleFunctionSet(self.object())

    def __hash__(self):
        """
        Private method that returns a hashable value for this instance.

        :rtype: int
        """

        return int(self.hashCode())

    def __eq__(self, other):
        """
        Private method that evaluates the equivalence between two objects.

        :param other: Value to test if equivalent with this instance.
        :type other: Union[str, om.MObject, om.MDagPath, NodeMixin]
        :rtype: bool
        """

        # Check value type
        #
        if isinstance(other, string_types):

            return self.name().lower().endswith(other.lower())

        elif isinstance(other, om.MObject):

            return self.object().__eq__(other)

        elif isinstance(other, om.MDagPath):

            return self.object().__eq__(other.node())

        elif isinstance(other, self.__class__) or issubclass(other.__class__, self.__class__):

            return self.object().__eq__(other.object())

        else:

            return False

    def __ne__(self, other):
        """
        Private method that evaluates the inequivalence between two objects.

        :param other: Value to test if not equivalent with this instance.
        :type other: Union[str, om.MObject, om.MDagPath, NodeMixin]
        :rtype: bool
        """

        # Check value type
        #
        if isinstance(other, string_types):

            return not self.name().lower().endswith(other.lower())

        elif isinstance(other, om.MObject):

            return self.object().__ne__(other)

        elif isinstance(other, om.MDagPath):

            return self.object().__ne__(other.node())

        elif isinstance(other, self.__class__) or issubclass(other.__class__, self.__class__):

            return self.object().__ne__(other.object())

        else:

            return True

    def __getattr__(self, name):
        """
        Private method used to intercept attribute calls that to do not exist.
        If the attribute is related to an API function sets then that attribute is returned instead.
        If not then a attribute error will be raised!

        :type name: str
        :return: See function set for details...
        """

        # Check if function set contains attribute
        #
        obj = getattr(self, '__functionset__')

        if not hasattr(obj, name):

            raise AttributeError('Unable to locate attribute: %s!' % name)

        # Check if attribute is callable
        #
        functionSet = obj(self.object())
        attribute = getattr(functionSet, name)

        if callable(attribute):

            # Define function wrapper
            #
            def wrapper(*args, **kwargs):

                log.debug('%s was called with %s args and %s kwargs.' % (name, args, kwargs))
                return attribute(*args, **kwargs)

            return wrapper

        else:

            return attribute

    def isInitialized(self):
        """
        Evaluates if this instance has already been initialized.

        :rtype: bool
        """

        return hasattr(self, '__handle__')

    def handle(self):
        """
        Returns the object handle associated with this instance.

        :rtype: om.MObjectHandle
        """

        return self.__handle__

    def hashCode(self):
        """
        Returns the hash code associated with this instance.

        :rtype: int
        """

        return self.__handle__.hashCode()

    def isAlive(self):
        """
        Evaluates whether this object still exists.

        :rtype: bool
        """

        return self.__handle__.isAlive()

    def object(self):
        """
        Returns the object associated with this instance.

        :rtype: om.MObject
        """

        return self.__handle__.object()

    def hasFn(self, apiType):
        """
        Evaluates whether this instance is derived from the supplied api type.

        :type apiType: int
        :rtype: bool
        """

        return self.object().hasFn(apiType)

    def apiType(self):
        """
        Returns the api type associated with this instance.

        :rtype: int
        """

        return self.object().apiType()

    @property
    def apiTypeStr(self):
        """
        Getter method that returns the api type as a human readable string.

        :rtype: str
        """

        return self.object().apiTypeStr

    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnDependencyNode
        """

        return self.__functionset__.__call__(self.object())

    def weakReference(self):
        """
        Returns a weak reference for this wrapper.

        :rtype: weakref.ref
        """

        return weakref.ref(self)

    @classproperty
    def className(cls):
        """
        Retrieves the name of this class.

        :rtype: str
        """

        return cls.__name__

    @classproperty
    def moduleName(cls):
        """
        Retrieves the name of the module this class is derived from.

        :rtype: str
        """

        return cls.__module__

    @classmethod
    def isAbstractClass(cls):
        """
        Evaluates whether this is an abstract class.

        :rtype: bool
        """

        return inspect.isabstract(cls)

    @classmethod
    def inheritanceDepth(cls):
        """
        Evaluates the number of overloads that make up this class.

        :rtype: int
        """

        return len(inspect.getmro(cls))

    @classmethod
    def findCompatibleFunctionSet(cls, dependNode):
        """
        Returns a function set that is compatible with the given dependency node.
        Since function sets use inheritance we don't need to worry about the base classes.

        :type dependNode: om.MObject
        :rtype: type
        """

        # Check if this type has already been looked up
        #
        apiType = dependNode.apiType()
        functionSet = cls.__functionsets__.get(apiType, None)

        if functionSet is not None:

            return functionSet

        # Collect function sets and sort by number of inheritance
        #
        functionSets = [x for x in dagutils.iterFunctionSets() if x().hasObj(dependNode)]
        functionSets.sort(key=lambda x: len(inspect.getmro(x)))

        cls.__functionsets__[apiType] = functionSets[-1]

        return cls.__functionsets__[apiType]
