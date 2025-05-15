from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PickMatrixMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with pick matrix nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kPickMatrix
    # endregion

    # region Attributes
    inputMatrix = mpyattribute.MPyAttribute('inputMatrix')
    useTranslate = mpyattribute.MPyAttribute('useTranslate')
    useRotate = mpyattribute.MPyAttribute('useRotate')
    useScale = mpyattribute.MPyAttribute('useScale')
    useShear = mpyattribute.MPyAttribute('useShear')
    outputMatrix = mpyattribute.MPyAttribute('outputMatrix')
    # endregion
