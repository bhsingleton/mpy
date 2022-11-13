from maya.api import OpenMaya as om
from .. import mpyattribute
from ..nodetypes import locatormixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PointHelperMixin(locatormixin.LocatorMixin):
    """
    Overload of LocatorMixin that interfaces with bone geometry shapes.
    """

    # region Dunderscores
    __plugin__ = 'pointHelper'
    # endregion

    # region Attributes
    centerMarker = mpyattribute.MPyAttribute('centerMarker')
    axisTripod = mpyattribute.MPyAttribute('axisTripod')
    cross = mpyattribute.MPyAttribute('cross')
    square = mpyattribute.MPyAttribute('square')
    box = mpyattribute.MPyAttribute('box')
    pyramid = mpyattribute.MPyAttribute('pyramid')
    diamond = mpyattribute.MPyAttribute('diamond')
    disc = mpyattribute.MPyAttribute('disc')
    arrow = mpyattribute.MPyAttribute('arrow')
    notch = mpyattribute.MPyAttribute('notch')
    tearDrop = mpyattribute.MPyAttribute('tearDrop')
    cylinder = mpyattribute.MPyAttribute('cylinder')
    sphere = mpyattribute.MPyAttribute('sphere')
    custom = mpyattribute.MPyAttribute('custom')
    size = mpyattribute.MPyAttribute('size')
    choice = mpyattribute.MPyAttribute('choice')
    text = mpyattribute.MPyAttribute('text')
    fontSize = mpyattribute.MPyAttribute('fontSize')
    lineWidth = mpyattribute.MPyAttribute('lineWidth')
    controlPoints = mpyattribute.MPyAttribute('controlPoints')
    fill = mpyattribute.MPyAttribute('fill')
    shaded = mpyattribute.MPyAttribute('shaded')
    drawOnTop = mpyattribute.MPyAttribute('drawOnTop')
    objectMatrix = mpyattribute.MPyAttribute('objectMatrix')
    # endregion
