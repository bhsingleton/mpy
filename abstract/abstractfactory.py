from abc import ABCMeta, abstractmethod

from . import singleton
from ..decorators import classproperty
from ..utilities import pyutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractFactory(singleton.Singleton):
    """
    Overload of Singleton used to outline factory behaviour.
    """

    __metaclass__ = ABCMeta
    __slots__ = ('__classes__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(AbstractFactory, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self.__classes__ = {x: y for (x, y) in self.iterClasses()}

    @classproperty
    def nullWeakReference(cls):
        """
        Returns a null weak reference that is still callable.

        :rtype: lambda
        """

        return lambda: None

    @abstractmethod
    def packages(self):
        """
        Returns a list of packages to be searched for factory classes.

        :rtype: list[module]
        """

        pass

    @abstractmethod
    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: class
        """

        pass

    def classAttr(self):
        """
        Returns the attribute name to be used to organize the class dictionary.
        By default this is set to '__name__' but you can change this to whatever you want.

        :rtype: str
        """

        return '__name__'

    def classes(self):
        """
        Returns a dictionary of classes that can be instantiated.
        The structure of this dictionary is dictated by the classAttr method!

        :rtype: dict[str:class]
        """

        return self.__classes__

    def iterModules(self):
        """
        Returns a generator that can iterate over all of the package modules.

        :rtype: iter
        """

        for package in self.packages():

            yield from pyutils.iterPackage(package)

    def iterItems(self):
        """
        Returns a generator that can iterate over all of the module contents.

        :rtype: iter
        """

        classFilter = self.classFilter()

        for module in self.iterModules():

            yield from pyutils.iterModule(module, classFilter=classFilter)

    def iterClasses(self):
        """
        Generator method used to iterate through all of the module items.

        :rtype: iter
        """

        # Iterate through module items
        #
        classAttr = self.classAttr()

        for (name, cls) in self.iterItems():

            # Check if class has required key identifier
            #
            if not hasattr(cls, classAttr):

                continue

            # Yield key-value pair
            #
            key = getattr(cls, classAttr)

            if isinstance(key, (tuple, list)):

                for item in key:

                    yield item, cls

            else:

                yield key, cls

    def getClass(self, key):
        """
        Returns a class constructor based on the supplied key.

        :type key: Union[str, int]
        :rtype: class
        """

        return self.__classes__.get(key, None)
