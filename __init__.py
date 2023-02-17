import os
import sys

import logging
logging.basicConfig()
log = logging.getLogger('mpy')
log.setLevel(logging.INFO)


def rollback(*paths):
    """
    Removes all modules, derived from the mpy package, from the system module.
    This will force any future imported modules to recompile.

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

        if filePath is None:

            continue

        # Check if module is derived from any of the supplied paths
        #
        filePath = os.path.abspath(os.path.normpath(filePath))

        if any([filePath.startswith(path) for path in paths]):

            log.info('Rolling back module: %s' % module)
            del sys.modules[moduleName]


def restart():
    """
    Restarts the entire mpy package.
    This method should only be used by developers when iterating on changes.

    :rtype: None
    """

    rollback(os.path.dirname(os.path.abspath(__file__)))
