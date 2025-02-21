import inspect
import weakref

from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils
from dcc.decorators.classproperty import classproperty
from dcc.vendor.six import string_types
from . import mabcmeta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MObjectWrapper(object, metaclass=mabcmeta.MABCMeta):
    """
    Abstract base class used as a low-level wrapper for Maya scene objects.
    Abstract base class used as a low-level wrapper for Maya scene objects.
    A lot of the architecture in this class is designed around dynamically looking up compatible function sets.
    If this class detects an unknown attribute it will attempt to resolve it through the function set.
    """

    # region Dunderscores
    __slots__ = ('__weakref__', '__handle__', '__function_set__')
    __function_sets__ = {}

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance has been created.

        :type obj: Union[str, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: None
        """

        # Call parent method
        #
        super(MObjectWrapper, self).__init__()

        # Declare private variables
        #
        self.__handle__ = dagutils.getMObjectHandle(obj)
        self.__function_set__ = self.findCompatibleFunctionSet(self.object())

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after this instance has been initialized.

        :rtype: None
        """

        pass
    
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

    def __getattribute__(self, name):
        """
        Private method that performs attribute accesses for instances of this class.
        If the attribute is related to an API function sets then that attribute is returned instead.

        :type name: str
        :return: Any
        """

        try:

            return super(MObjectWrapper, self).__getattribute__(name)

        except AttributeError:

            cls = super(MObjectWrapper, self).__getattribute__('__function_set__')
            func = super(MObjectWrapper, self).__getattribute__('object')
            functionSet = cls(func())

            return getattr(functionSet, name)
    # endregion

    # region Properties
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

    @property
    def apiTypeStr(self):
        """
        Getter method that returns the api type as a human readable string.

        :rtype: str
        """

        return self.object().apiTypeStr
    # endregion

    # region Methods
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

    def hasFn(self, *apiTypes):
        """
        Evaluates whether this instance is derived from the supplied api type.

        :type apiTypes: Union[int, List[int]]
        :rtype: bool
        """

        return any(map(self.object().hasFn, apiTypes))

    def apiType(self):
        """
        Returns the api type associated with this instance.

        :rtype: int
        """

        return self.object().apiType()

    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnDependencyNode
        """

        return self.__function_set__.__call__(self.object())

    def weakReference(self):
        """
        Returns a weak reference for this wrapper.

        :rtype: weakref.ref
        """

        return weakref.ref(self)

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
        functionSet = cls.__function_sets__.get(apiType, None)

        if functionSet is not None:

            return functionSet

        # Collect function sets and sort by inheritance depth
        #
        functionSets = [x for x in dagutils.iterFunctionSets() if x().hasObj(dependNode)]
        functionSets.sort(key=lambda x: len(inspect.getmro(x)))

        functionSet = functionSets[-1]
        cls.__function_sets__[apiType] = functionSet

        return functionSet
    # endregion
