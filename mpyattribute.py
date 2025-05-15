from maya import OpenMaya as legacy
from maya.api import OpenMaya as om
from dcc.maya.libs import plugutils, plugmutators

from . import mpynode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyAttribute(object):
    """
    Base class used to represent Maya attributes as a python property.
    If a different context is required to access attributes be sure to use a `MPyContext` statement!
    """

    __slots__ = (
        'name',
        'constructors',
        'fget',
        'fset',
        'fdel',
        'fchange'
    )

    def __init__(self, name, fget=None, fset=None, fdel=None, **constructors):
        """
        Private method called after a new instance has been created.

        :type name: str
        :type fget: Callable
        :type fset: Callable
        :type fdel: Callable
        :key readable: bool
        :key writable: bool
        :key storable: bool
        :key keyable: bool
        :key attributeType: str
        :rtype: None
        """

        # Call parent method
        #
        super(MPyAttribute, self).__init__()

        # Store reference to attribute
        #
        self.name = name
        self.constructors = constructors
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.fchange = None

    def __get__(self, instance, owner):
        """
        Private method called whenever the user attempts to retrieve this property.

        :type instance: mpynode.MPyNode
        :type owner: class
        :rtype: Any
        """

        # Check if instance was supplied
        #
        if instance is None:

            return self

        # Get plug value
        #
        value = plugmutators.getValue(self.plug(instance))

        if callable(self.fget):

            return self.fget(instance, value)

        else:

            return value

    def __set__(self, instance, value):
        """
        Private method called whenever the user attempts to update this property.

        :type instance: mpynode.MPyNode
        :type value: Any
        :rtype: None
        """

        # Check if instance is valid
        #
        if instance is None:

            return

        # Update plug value
        #
        if callable(self.fset):

            value = self.fset(instance, value)

        plugmutators.setValue(self.plug(instance), value)

        # Notify change
        #
        if callable(self.fchange):

            self.fchange(instance, value)

    def __delete__(self, instance):
        """
        Private method called whenever the user attempts to delete this property.

        :type instance: mpynode.MPyNode
        :rtype: None
        """

        # Check if instance is valid
        #
        if instance is None:

            return

        # Reset plug value
        #
        if callable(self.fdel):

            self.fdel(instance)

        plugmutators.resetValue(self.plug(instance))

    def plug(self, instance):
        """
        Returns the plug associated with the given instance.

        :type instance: mpynode.MPyNode
        :rtype: om.MPlug
        """

        # Check instance type
        #
        if isinstance(instance, mpynode.MPyNode):

            return plugutils.findPlug(instance.object(), self.name)

        else:

            raise TypeError('plug() expects an MPyNode (%s given)' % type(instance).__name__)

    def validateAndGetValue(self, func):
        """
        Function decorator used to intercept getter operations.

        :type func: function
        :rtype: None
        """

        # Check if object is callable
        #
        if callable(func):

            self.fget = func

        return self

    def validateAndSetValue(self, func):
        """
        Function decorator used to intercept setter operations.

        :type func: function
        :rtype: None
        """

        # Check if object is callable
        #
        if callable(func):

            self.fset = func

        return self

    def validateAndResetValue(self, func):
        """
        Function decorator used to intercept delete operations.

        :type func: function
        :rtype: None
        """

        # Check if object is callable
        #
        if callable(func):

            self.fdel = func

        return self

    def changed(self, func):
        """
        Function decorator used to intercept changes made to this attribute.

        :type func: function
        :rtype: None
        """

        # Check if object is callable
        #
        if callable(func):

            self.fchange = func

        return self

    def notify(self, instance):
        """
        Forces the changed event to be evoked even if the value hasn't been set.

        :type instance: mpy.mpynode.MPyNode
        :rtype: None
        """

        if callable(self.fchange):

            self.fchange(instance, self.__get__(instance, type(instance)))
