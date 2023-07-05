from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import aimconstraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class LookAtMixin(aimconstraintmixin.AimConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with look-at constraints.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kLookAt
    # endregion
