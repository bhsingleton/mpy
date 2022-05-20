from maya.api import OpenMaya as om
from dcc.maya.libs import plugmutators

from . import mpynode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyContext(object):
    """
    Execution hook that can be used with a 'with' statement in order to alter the MDGContext at runtime.
    This allows PyAttribute objects to evaluate the DAG at a different time.
    """

    __slots__ = ('time', 'context')

    def __init__(self, time):
        """
        Private method called after a new instance is created.

        :type time: Union[int, float]
        :rtype: None
        """

        # Call parent method
        #
        super(MPyContext, self).__init__()

        # Declare class variables
        #
        self.time = time
        self.context = om.MDGContext(time)

    def __enter__(self):
        """
        Private method called before a block of code is executed.

        :rtype: None
        """

        MPyAttribute.__context__ = self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method called after a block of code has been executed.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: str
        :rtype: None
        """

        MPyAttribute.__context__ = om.MDGContext.kNormal


class MPyAttribute(object):
    """
    Base class used to represent Maya attributes as a python property.
    With this approach there is no MDGContext support so support is limited to non-keyable attributes!
    You could use an entry/exit point to mitigate this drawback if needed?
    """

    __slots__ = ('name', 'fget', 'fset', 'fdel', 'fchange')
    __context__ = om.MDGContext.kNormal

    def __init__(self, name, fget=None, fset=None, fdel=None):
        """
        Private method called after a new instance has been created.

        :type name: str
        :type fget: function
        :type fset: function
        :type fdel: function
        :rtype: None
        """

        # Call parent method
        #
        super(MPyAttribute, self).__init__()

        # Store reference to attribute
        #
        self.name = name

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

        # Check if instance is valid
        #
        if instance is None:

            return self

        # Retrieve plug value
        #
        value = plugmutators.getValue(self.plug(instance), context=self.__context__)

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
        if callable(self.fset):

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

            return om.MPlug(instance.object(), instance.attribute(self.name))

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

    def resetValue(self, func):
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
