from maya.api import OpenMaya as om
from .. import mpyattribute
from ..nodetypes import locatormixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BoneGometryMixin(locatormixin.LocatorMixin):
    """
    Overload of `LocatorMixin` that interfaces with bone geometry nodes.
    """

    # region Attributes
    width = mpyattribute.MPyAttribute('width')
    height = mpyattribute.MPyAttribute('height')
    length = mpyattribute.MPyAttribute('length')
    taper = mpyattribute.MPyAttribute('taper')
    sideFins = mpyattribute.MPyAttribute('sideFins')
    sideFinsSize = mpyattribute.MPyAttribute('sideFinsSize')
    sideFinsStartTaper = mpyattribute.MPyAttribute('sideFinsStartTaper')
    sideFinsEndTaper = mpyattribute.MPyAttribute('sideFinsEndTaper')
    frontFin = mpyattribute.MPyAttribute('frontFin')
    frontFinSize = mpyattribute.MPyAttribute('frontFinSize')
    frontFinStartTaper = mpyattribute.MPyAttribute('frontFinStartTaper')
    frontFinEndTaper = mpyattribute.MPyAttribute('frontFinEndTaper')
    backFin = mpyattribute.MPyAttribute('backFin')
    backFinSize = mpyattribute.MPyAttribute('backFinSize')
    backFinStartTaper = mpyattribute.MPyAttribute('backFinStartTaper')
    backFinEndTaper = mpyattribute.MPyAttribute('backFinEndTaper')
    objectMatrix = mpyattribute.MPyAttribute('objectMatrix')
    # endregion

    # region Dunderscores
    __plugin__ = 'boneGeometry'
    # endregion
