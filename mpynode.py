from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils
from dcc.decorators.classproperty import classproperty
from .abstract import mabcmeta, mobjectwrapper

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyNode(mobjectwrapper.MObjectWrapper, metaclass=mabcmeta.MABCMeta):
    """
    Overload of `MObjectWrapper` that acts as a base class for all Maya node interfaces.
    See `__accepts__` dunderscore for a list of supported types to initialize from.
    In order to register a new interface developers should override either the `__api_type__` for builtins or `__plugin__` for plugins!
    """

    # region Dunderscores
    __api_type__ = om.MFn.kBase
    __scene__ = None

    def __new__(cls, obj, **kwargs):
        """
        Private method called before a new instance is created.
        This method is responsible for moderating the instantiation of valid dependency nodes.

        :type obj: Union[str, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: MPyNode
        """

        # Evaluate object type
        #
        if not isinstance(obj, cls.__accepts__):

            raise TypeError('MPyNode() expects %s (%s given)!' % (cls.__accepts__, type(obj).__name__))

        # Check if supplied object is valid
        #
        handle = dagutils.getMObjectHandle(obj)

        if handle.isAlive():

            # Create new instance
            # Don't forget to replace the base class with the correct interface!
            #
            instance = super(MPyNode, cls).__new__(cls)
            instance.__class__ = cls.scene.getClass(handle.object())

            return instance

        else:

            return None
    # endregion

    # region Properties
    @classproperty
    def scene(cls):
        """
        Returns the node factory class.
        It's a bit hacky but this way we can bypass cyclical import errors.

        :rtype: mpy.mpyscene.MPyScene
        """

        # Check if scene interface exists
        #
        if cls.__scene__ is None:

            from . import mpyscene
            cls.__scene__ = mpyscene.MPyScene.getInstance(asWeakReference=True)

        return cls.__scene__()
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

            raise TypeError(f'isCompatible() expects an MObject ({type(dependNode).__name__} given)!')

        # Check api type
        #
        apiType = cls.__api_type__

        if isinstance(apiType, int):

            return dependNode.hasFn(apiType)

        elif isinstance(apiType, (list, tuple)):

            return any(map(dependNode.hasFn, apiType))

        else:

            raise TypeError(f'isCompatible() expects a valid type constant ({type(apiType).__name__} given)!')

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

        return cls.scene.createNode(typeName, name=name, parent=parent, skipSelect=skipSelect)

    def hasExtension(self):
        """
        Evaluates if this instance has an extension.

        :rtype: bool
        """

        return self.scene.isExtension(self.object())

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
        self.__class__ = self.scene.createExtensionClass(self.__class__, extensionClass)
        self.__init__(self.object())
        self.__post_init__()

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
        self.__class__ = self.scene.getClass(self.object())

    def delete(self):
        """
        Removes this instance from the scene file.
        Be careful calling any instance method after deleting this node.
        Any references to a null pointer will result in a crash!

        :rtype: None
        """

        dagutils.deleteNode(self.object())
    # endregion
