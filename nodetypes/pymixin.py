import maya.cmds as mc
import maya.api.OpenMaya as om

from abc import ABCMeta, abstractmethod

from . import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PyMixin(dependencymixin.DependencyMixin, metaclass=ABCMeta):
    """
    Overload of DependencyMixin used to create a pythonic node extensions for Maya.
    If your class requires data storage be sure to overload the createUserAttributes method.
    The PyAttribute class can used to create accessors to those user attributes.
    """

    __apitype__ = om.MFn.kPluginDependNode
    __plugin__ = 'pyNode'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(PyMixin, self).__init__(*args, **kwargs)

        # Create user attributes
        #
        self.createUserAttributes()

    @classmethod
    def creator(cls, **kwargs):
        """
        Returns a new PyNode referencing this class for the constructor arguments.
        This is done by modifying the attribute values before passing to the pyFactory.

        :rtype: PyMixin
        """

        # Create pyNode and define constructors
        #
        partialPathName = mc.createNode(cls.__plugin__, name=f'{cls.className}1')
        mc.setAttr(f'{partialPathName}.__name__', cls.className, type='string')
        mc.setAttr(f'{partialPathName}.__module__', cls.moduleName, type='string')

        return cls.pyFactory(partialPathName)

    @abstractmethod
    def createUserAttributes(self):
        """
        Assigns any user attributes required for data storage.
        I highly suggest using an attribute template to automate this process.

        :rtype dict[str:om.MObjectHandle]
        """

        return {}
