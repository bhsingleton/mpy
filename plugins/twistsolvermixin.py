from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TwistSolverMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with twist-solver nodes.
    """

    # region Dunderscores
    __plugin__ = 'twistSolver'
    # endregion

    # region Attributes
    segments = mpyattribute.MPyAttribute('segments')
    inCurve = mpyattribute.MPyAttribute('inCurve')
    forwardAxis = mpyattribute.MPyAttribute('forwardAxis')
    forwardAxisFlip = mpyattribute.MPyAttribute('forwardAxisFlip')
    upAxis = mpyattribute.MPyAttribute('upAxis')
    upAxisFlip = mpyattribute.MPyAttribute('upAxisFlip')
    inverse = mpyattribute.MPyAttribute('inverse')
    reverse = mpyattribute.MPyAttribute('reverse')
    falloffEnabled = mpyattribute.MPyAttribute('falloffEnabled')
    falloff = mpyattribute.MPyAttribute('falloff')
    startMatrix = mpyattribute.MPyAttribute('startMatrix')
    startOffsetMatrix = mpyattribute.MPyAttribute('startOffsetMatrix')
    endMatrix = mpyattribute.MPyAttribute('endMatrix')
    endOffsetMatrix = mpyattribute.MPyAttribute('endOffsetMatrix')
    # endregion
