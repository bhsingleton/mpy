from maya.api import OpenMaya as om
from enum import IntEnum
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InputType(IntEnum):
    """
    Enum class of all available RBF input types.
    """

    EUCLIDEAN = 0
    QUATERNION = 1


class Function(IntEnum):
    """
    Enum class of all available RBF functions.
    """
    LINEAR = 0
    GAUSSIAN = 1
    THIN_PLATE = 2
    MULTI_QUADRATIC_BIHARMONIC = 3
    INVERSE_MULTI_QUADRATIC_BIHARMONIC = 4
    BECKERT_WENDLAND_C2_BASIC = 5


class RBFSolverMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with RBF solvers.
    """

    # region Attributes
    inputType = mpyattribute.MPyAttribute('inputType')
    function = mpyattribute.MPyAttribute('function')
    radius = mpyattribute.MPyAttribute('radius')
    regularization = mpyattribute.MPyAttribute('regularization')
    debug = mpyattribute.MPyAttribute('debug')
    sample = mpyattribute.MPyAttribute('sample')
    outputTranslate = mpyattribute.MPyAttribute('outputTranslate')
    outputRotate = mpyattribute.MPyAttribute('outputRotate')
    outputScale = mpyattribute.MPyAttribute('outputScale')
    # endregion

    # region Dunderscores
    __plugin__ = 'rbfSolver'
    # endregion
