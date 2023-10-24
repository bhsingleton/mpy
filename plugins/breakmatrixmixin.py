from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BreakMatrixMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with break-matrix nodes.
    """

    # region Dunderscores
    __plugin__ = 'breakMatrix'
    # endregion

    # region Attributes
    normalize = mpyattribute.MPyAttribute('normalize')
    inMatrix = mpyattribute.MPyAttribute('inMatrix')
    row1 = mpyattribute.MPyAttribute('row1')
    row2 = mpyattribute.MPyAttribute('row2')
    row3 = mpyattribute.MPyAttribute('row3')
    row4 = mpyattribute.MPyAttribute('row4')
    # endregion
