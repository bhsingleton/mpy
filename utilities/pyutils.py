import os
import sys
import inspect

try:

    reload  # Python 2: "reload" is built-in

except NameError:

    from importlib import reload

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getStringTypes():
    """
    Returns a list of string types based on the version of python.

    :rtype: tuple
    """

    if sys.version_info[0] == 2:

        return basestring, str, unicode

    else:

        return str


def resolveFilePath(filePath):
    """
    Converts a file path into a module path compatible with import statements.

    :type filePath: str
    :rtype: str
    """

    # Normalize file paths
    #
    pythonPaths = [os.path.normpath(x) for x in sys.path]
    filePath = os.path.normpath(os.path.expandvars(filePath))

    if filePath.endswith('__init__.py') or filePath.endswith('__init__.pyc'):

        filePath = os.path.dirname(filePath)

    elif os.path.isfile(filePath):

        filePath, extension = os.path.splitext(filePath)

    else:

        pass

    # Collect paths that are relative
    #
    found = [x for x in pythonPaths if filePath.startswith(x)]
    numFound = len(found)

    if numFound == 0:

        return ''

    # Join strings using module delimiter
    #
    startPath = max(found)
    relativePath = os.path.relpath(filePath, startPath)

    return '.'.join(relativePath.split(os.sep))


def importFile(filePath):
    """
    Imports the package/module from the supplied file path.

    :type filePath: str
    :rtype: Union[package, module]
    """

    # Check file type
    #
    if not isinstance(filePath, str):

        raise TypeError('importFile() expects a str (%s given)!' % type(filePath).__name__)

    # Check if file exists
    #
    if not os.path.exists(filePath):

        raise TypeError('importFile() expects a valid file!')

    # Import module
    #
    return __import__(
        resolveFilePath(filePath),
        locals=locals(),
        globals=globals(),
        fromlist=[filePath],
        level=0
    )


def iterPackage(package, forceReload=False):
    """
    Returns a generator that yields all of the modules from the given package.
    If the supplied path does not exist then a type error will be raised!
    The level flag indicates the import operation: -1: best guess, 0: absolute, 1: relative

    :type package: str
    :type forceReload: bool
    :rtype: iter
    """

    # Check if this is a file
    #
    if isinstance(package, str):

        package = importFile(package)

    # Iterate through module files inside package
    #
    directory = os.path.dirname(package.__path__[0])

    for filename in os.listdir(directory):

        # Verify this is a module
        #
        moduleName, extension = os.path.splitext(filename)

        if moduleName == '__init__' or extension != '.py':

            continue

        # Try and import module
        #
        filePath = os.path.join(directory, '%s.py' % moduleName)

        modulePath = resolveFilePath(filePath)
        log.info('Attempting to import: "%s" module, from: %s' % (modulePath, filePath))

        try:

            # Import module and check if it should be reloaded
            #
            module = importFile(filePath)

            if forceReload:

                log.info('Reloading module...')
                reload(module)

            yield module

        except ImportError as exception:

            log.warning(exception)
            continue


def iterModule(module, includeAbstract=False, classFilter=object):
    """
    Generator method used to iterate through all of the classes inside a module.
    An optional subclass filter can be provided to ignore certain types.

    :type module: module
    :type includeAbstract: bool
    :type classFilter: type
    :rtype: iter
    """

    # Iterate through module dictionary
    #
    for (key, item) in module.__dict__.items():

        # Verify this is a class
        #
        if not inspect.isclass(item):

            continue

        # Check if this is a abstract class
        #
        if inspect.isabstract(item) and not includeAbstract:

            continue

        # Check if this is a subclass of abstract node
        #
        if issubclass(item, classFilter) or item is classFilter:

            yield key, item

        else:

            log.debug('Skipping %s class...' % key)


def findClass(className, modulePath):
    """
    Returns the class associated with the given string.
    To improve the results be sure to provide a class name complete with module path.

    :type className: str
    :type modulePath: str
    :rtype: class
    """

    # Check if string is valid
    #
    if len(className) == 0:

        return None

    # Split string using delimiter
    #
    if len(modulePath) == 0:

        return globals().get(className, None)

    else:

        module = sys.modules.get(modulePath, None)
        root = modulePath.split('.', 1)[0]

        if module is None:

            module = __import__(modulePath, locals=locals(), globals=globals(), fromlist=[root], level=0)

        return module.__dict__.get(className, None)


string_types = getStringTypes()
