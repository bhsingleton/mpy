from abc import ABCMeta
from maya.api import OpenMaya as om
from dcc.maya.libs import dagutils
from dcc.vendor.six import integer_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MABCMeta(ABCMeta):
    """
    Maya abstract base class that supports post-initialization.
    """

    # region Dunderscores
    __slots__ = ()
    __accepts__ = (str, om.MUuid, om.MObjectHandle, om.MObject, om.MDagPath)
    __instances__ = {}

    def __call__(cls, obj, **kwargs):
        """
        Private method that's called whenever this class is evoked.

        :rtype: MABCMeta
        """

        # Redundancy check
        #
        if type(obj).__class__ is MABCMeta:

            return obj

        # Evaluate object type
        #
        if isinstance(obj, cls.__accepts__):

            # Check if instance already exists
            #
            handle = dagutils.getMObjectHandle(obj)
            instance = cls.getInstance(handle)

            if instance is not None:

                return instance

            # Create new instance
            #
            instance = super(MABCMeta, cls).__call__(obj, **kwargs)

            if instance is not None:

                instance.__post_init__(obj, **kwargs)
                cls.__instances__[instance.hashCode()] = instance

            return instance

        elif isinstance(obj, integer_types):

            # Lookup hashed instance
            #
            return cls.__instances__.get(obj, None)

        else:

            raise TypeError(f'{cls.__name__}() expects {cls.__accepts__} ({type(obj).__name__} given)!')
    # endregion

    # region Methods
    def getInstance(cls, handle):
        """
        Returns an instance associated with the given object handle.

        :type handle: om.MObjectHandle
        :rtype: MABCMeta
        """

        # Check if object handle is alive
        #
        if not handle.isAlive():

            return None

        # Check if handle has been registered
        #
        hashCode = handle.hashCode()
        instance = cls.__instances__.get(hashCode, None)

        if instance is None:

            return None

        # Check if handle is still valid
        #
        if instance.isAlive():

            return instance

        else:

            del cls.__instances__[hashCode]
            return None
    # endregion
