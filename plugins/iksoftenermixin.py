from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKSoftenerMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with IK softeners.
    """

    # region Attributes
    envelope = mpyattribute.MPyAttribute('envelope')
    startMatrix = mpyattribute.MPyAttribute('startMatrix')
    endMatrix = mpyattribute.MPyAttribute('endMatrix')
    radius = mpyattribute.MPyAttribute('radius')
    chainLength = mpyattribute.MPyAttribute('chainLength')
    chainScaleCompensate = mpyattribute.MPyAttribute('chainScaleCompensate')
    parentInverseMatrix = mpyattribute.MPyAttribute('parentInverseMatrix')
    # endregion

    # region Dunderscores
    __plugin__ = 'ikSoftener'
    # endregion
