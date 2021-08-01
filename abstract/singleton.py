import weakref

from abc import ABCMeta, abstractmethod

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Singleton(object):
    """
    Abstract class used to define a singleton pattern for python classes.
    """

    __metaclass__ = ABCMeta
    __slots__ = ('__weakref__',)
    __instances__ = {}

    def __new__(cls, *args, **kwargs):
        """
        Overloaded method called before a new instance is created.
        """

        # Check if instance already exists
        #
        if not cls.hasInstance():

            cls.__instances__[cls.__name__] = super(Singleton, cls).__new__(cls)

        return cls.__instances__[cls.__name__]

    def __init__(self, *args, **kwargs):
        """
        Overloaded method called after a new instance has been created.
        """

        # Call parent method
        #
        super(Singleton, self).__init__()

    def weakReference(self):
        """
        Method used to retrieve a weak reference for this instance.
        This will make garbage collection easier by reducing the number of physical references.

        :rtype: weakref.ref
        """

        return weakref.ref(self)

    @classmethod
    def creator(cls, *args, **kwargs):
        """
        Class method used to create a new instance of this class.
        This method is intended to overloaded in case subclasses require additional parameters to initialize.

        :rtype: Singleton
        """

        return cls()

    @classmethod
    def hasInstance(cls):
        """
        Class method used to determine if this class already has an instance.

        :rtype: bool
        """

        return cls.__instances__.get(cls.__name__, None) is not None

    @classmethod
    def getInstance(cls):
        """
        Class method used to retrieve an instance of this class.

        :rtype: Singleton
        """

        # Get instance from class name
        #
        instance = cls.__instances__.get(cls.__name__, None)

        if instance is None:

            instance = cls.creator()
            cls.__instances__[instance.__class__.__name__] = instance

        return instance
