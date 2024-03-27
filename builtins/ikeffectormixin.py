from maya.api import OpenMaya as om
from . import transformmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKEffectorMixin(transformmixin.TransformMixin):
    """
    Overload of `TransformMixin` that interfaces with IK-effectors.
    """

    # region Attributes
    handlePath = mpyattribute.MPyAttribute('handlePath')
    hideDisplay = mpyattribute.MPyAttribute('hideDisplay')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kIkEffector
    # endregion
