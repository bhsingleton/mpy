from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TwistSolverMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with twist solvers.
    """

    # region Dunderscores
    __plugin__ = 'twistSolver'
    # endregion

    # region Attributes
    forwardAxis = mpyattribute.MPyAttribute('forwardAxis')
    forwardAxisFlip = mpyattribute.MPyAttribute('forwardAxisFlip')
    upAxis = mpyattribute.MPyAttribute('upAxis')
    upAxisFlip = mpyattribute.MPyAttribute('upAxisFlip')
    inverse = mpyattribute.MPyAttribute('inverse')
    reverse = mpyattribute.MPyAttribute('reverse')
    falloffEnabled = mpyattribute.MPyAttribute('falloffEnabled')
    falloff = mpyattribute.MPyAttribute('falloff')
    inCurve = mpyattribute.MPyAttribute('inCurve')
    segments = mpyattribute.MPyAttribute('segments')
    startMatrix = mpyattribute.MPyAttribute('startMatrix')
    startOffsetMatrix = mpyattribute.MPyAttribute('startOffsetMatrix')
    endMatrix = mpyattribute.MPyAttribute('endMatrix')
    endOffsetMatrix = mpyattribute.MPyAttribute('endOffsetMatrix')
    # endregion
