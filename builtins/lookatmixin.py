from maya.api import OpenMaya as om
from . import aimconstraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LookAtMixin(aimconstraintmixin.AimConstraintMixin):
    """
    Overload of `AimConstraintMixin` that interfaces with look-at constraints.
    """

    # region Attributes
    displayConnector = mpyattribute.MPyAttribute('displayConnector')
    distanceBetween = mpyattribute.MPyAttribute('distanceBetween')
    twist = mpyattribute.MPyAttribute('twist')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kLookAt
    # endregion
