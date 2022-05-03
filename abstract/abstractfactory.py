import inspect

from abc import abstractmethod
from dcc.decorators.classproperty import classproperty

from . import singleton
from ..utilities import pyutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractFactory(singleton.Singleton):
    """
    Overload of Singleton used to outline factory behaviour.
    """

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
        self.__classes__ = dict(self.iterPackages(*self.packages()))

    def __iter__(self):
        """
        Private method that returns a generator that yields all available classes.

        :rtype: iter
        """

        return self.iterPackages(*self.packages())

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, str]
        :rtype: type
        """

        return self.getClass(key)

    def __len__(self):
        """
        Private method that evaluates the number of classes belonging to this factory.

        :rtype: int
        """

        pass

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
        Returns a list of packages to be inspected for classes.

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

        :rtype: dict[str:type]
        """

        return self.__classes__

    def getClass(self, key):
        """
        Returns a class constructor based on the supplied key.

        :type key: Union[str, int]
        :rtype: class
        """

        return self.__classes__.get(key, None)

    def iterModules(self, *args, **kwargs):
        """
        Returns a generator that yields all of the classes from the supplied modules.
        Optional keywords can be used to override the factory defaults.

        :key classAttr: str
        :key classFilter: type
        :rtype: iter
        """

        # Iterate through arguments
        #
        classAttr = kwargs.get('classAttr', self.classAttr())
        classFilter = kwargs.get('classFilter', self.classFilter())

        for arg in args:

            # Check if this is a module
            #
            if not inspect.ismodule(arg):

                continue

            # Iterate through module items
            #
            for (name, cls) in pyutils.iterModule(arg, classFilter=classFilter):

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

    def iterPackages(self, *args, **kwargs):
        """
        Returns a generator that yields all of the classes from the supplied packages.
        Optional keywords can be used to override the factory defaults.

        :rtype: iter
        """

        # Iterate through arguments
        #
        for arg in args:

            # Check if this is a package
            #
            if not inspect.ismodule(arg):

                continue

            # Iterate through modules
            #
            modules = list(pyutils.iterPackage(arg))

            for (key, cls) in self.iterModules(*modules, **kwargs):

                yield key, cls