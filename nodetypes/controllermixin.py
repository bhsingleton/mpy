from maya.api import OpenMaya as om
from . import dependencymixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ControllerMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with controller tags.
    """

    # region Attributes
    controllerObject = mpyattribute.MPyAttribute('controllerObject')
    cycleWalkSibling = mpyattribute.MPyAttribute('cycleWalkSibling')
    parent = mpyattribute.MPyAttribute('parent')
    children = mpyattribute.MPyAttribute('children')
    prepopulate = mpyattribute.MPyAttribute('prepopulate')
    parentprepopulate = mpyattribute.MPyAttribute('parentprepopulate')
    visibilityMode = mpyattribute.MPyAttribute('visibilityMode')
    #

    # region Dunderscores
    __api_type__ = om.MFn.kControllerTag
    # endregion
