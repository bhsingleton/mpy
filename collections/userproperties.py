import json

from maya import cmds as mc
from maya.api import OpenMaya as om
from six.moves import collections_abc
from dcc.maya.libs import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class UserProperties(collections_abc.MutableMapping):
    """
    Overload of MutableMapping that interfaces with user properties.
    """

    # region Dunderscores
    __slots__ = ('__handle__', '__properties__')

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance has been created.

        :type obj: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """
        # Call parent method
        #
        super(UserProperties, self).__init__()

        # Declare private variables
        #
        self.__handle__ = dagutils.getMObjectHandle(obj)
        self.__properties__ = {}

        # Reload user properties
        #
        self.reload()

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, str]
        :rtype: Any
        """

        return self.__properties__[key]

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[int, str]
        :type value: Any
        :rtype: None
        """

        self.__properties__[key] = value
        self.invalidate()

    def __delitem__(self, key):
        """
        Private method that removes an indexed item.

        :type key: Union[int, str]
        :rtype: None
        """

        del self.__properties__[key]
        self.invalidate()

    def __len__(self):
        """
        Private method that returns the number of properties.

        :rtype: int
        """

        return len(self.__properties__)

    def __iter__(self):
        """
        Private method that returns a generator that yields property keys.

        :rtype: iter
        """

        return iter(self.__properties__)
    # endregion

    # region Methods
    def object(self):
        """
        Returns the associated dependency node.

        :rtype: om.MObject
        """

        return self.__handle__.object()

    def objectName(self):
        """
        Returns the name of the associated dependency node.

        :rtype: str
        """

        return om.MFnDependencyNode(self.object()).name()

    def objectPath(self):
        """
        Returns the full name of the associated dependency node.

        :rtype: str
        """

        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            return om.MDagPath.getAPathTo(obj).fullPathName()

        else:

            return self.objectName()

    def keys(self):
        """
        Returns a generator that yields property keys.

        :rtype: iter
        """

        return self.__properties__.keys()

    def values(self):
        """
        Returns a generator that yields property values.

        :rtype: iter
        """

        return self.__properties__.values()

    def items(self):
        """
        Returns a generator that yields property key-value pairs.

        :rtype: iter
        """

        return self.__properties__.items()

    def update(self, items):
        """
        Copies the supplied items to the internal properties.

        :type items: dict
        :rtype: None
        """

        self.__properties__.update(items)
        self.invalidate()

    def ensureNotes(self):
        """
        Ensures that the supplied node has a notes attribute.

        :rtype: None
        """

        # Check if notes exist
        #
        fullPathName = self.objectPath()

        if not mc.attributeQuery('notes', node=fullPathName, exists=True):

            mc.addAttr(fullPathName, longName='notes', shortName='nts', dataType='string', cachedInternally=True)

    def buffer(self):
        """
        Returns the user property buffer from the notes plug.

        :rtype: str
        """

        self.ensureNotes()
        notes = mc.getAttr('%s.notes' % self.objectPath())

        if notes is not None:

            return notes

        else:

            return ''
    
    def setBuffer(self, buffer):
        """
        Updates the user property buffer.

        :type buffer: str
        :rtype: None
        """

        # Evaluate buffer size
        #
        if len(buffer) == 0:

            return

        # Ensure ".notes" exist
        #
        self.ensureNotes()

        # Load properties from buffer
        #
        try:

            self.__properties__ = json.loads(buffer)
            self.invalidate()

        except json.JSONDecodeError:

            self.__properties__ = {}
            self.invalidate()

    def reload(self):
        """
        Reloads the user properties from the current buffer.

        :rtype: None
        """

        self.setBuffer(self.buffer())

    def invalidate(self):
        """
        Dumps the user properties into the notes plug.

        :rtype: None
        """

        self.ensureNotes()

        if len(self.__properties__) > 0:

            notes = json.dumps(self.__properties__, indent=4)
            mc.setAttr('%s.notes' % self.objectPath(), notes, type='string')
    # endregion