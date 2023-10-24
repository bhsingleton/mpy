import os
import sys

from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger('mpy')
log.setLevel(logging.INFO)


def removeSystemModules(*paths):
    """
    Removes all the sys modules derived from the supplied directories.

    :type paths: Union[str, List[str]]
    :rtype: None
    """

    # Iterate through modules
    #
    moduleNames = set(sys.modules.keys())
    paths = [os.path.dirname(os.path.abspath(path)) if os.path.isfile(path) else os.path.abspath(path) for path in paths if os.path.exists(path)]

    for moduleName in moduleNames:

        # Get path to module
        #
        module = sys.modules[moduleName]
        filePath = getattr(module, '__file__', None)

        if not isinstance(filePath, string_types):

            continue

        # Check if module is derived from any of the supplied paths
        #
        absolutePath = os.path.abspath(os.path.normpath(filePath))

        if any([absolutePath.startswith(path) for path in paths]):

            log.info('Rolling back module: {module}')
            del sys.modules[moduleName]


def restart():
    """
    Restarts the entire mpy package.
    This method should only be used by developers when iterating on changes.

    :rtype: None
    """

    removeSystemModules(os.path.dirname(os.path.abspath(__file__)))
