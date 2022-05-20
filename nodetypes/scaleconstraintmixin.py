from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ScaleConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of ConstraintMixin that interfaces with orient constraints.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kScaleConstraint

    __targets__ = {
        'targetScaleX': 'scaleX',
        'targetScaleY': 'scaleY',
        'targetScaleZ': 'scaleZ',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintScaleCompensate': 'segmentScaleCompensate',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintScaleX': 'scaleX',
        'constraintScaleY': 'scaleY',
        'constraintScaleZ': 'scaleZ'
    }
    # endregion

    # region Attributes
    offset = mpyattribute.MPyAttribute('offset')
    offsetX = mpyattribute.MPyAttribute('offsetX')
    offsetY = mpyattribute.MPyAttribute('offsetY')
    offsetZ = mpyattribute.MPyAttribute('offsetZ')
    restScale = mpyattribute.MPyAttribute('restScale')
    restScaleX = mpyattribute.MPyAttribute('restScaleX')
    restScaleY = mpyattribute.MPyAttribute('restScaleY')
    restScaleZ = mpyattribute.MPyAttribute('restScaleZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        pass
    # endregion
