from maya.api import OpenMaya as om
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class OrientConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of ConstraintMixin that interfaces with orient constraints.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kOrientConstraint

    __targets__ = {
        'targetRotateX': 'rotateX',
        'targetRotateY': 'rotateY',
        'targetRotateZ': 'rotateZ',
        'targetRotateOrder': 'rotateOrder',
        'targetJointOrientX': 'jointOrientX',
        'targetJointOrientY': 'jointOrientY',
        'targetJointOrientZ': 'jointOrientZ',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintRotateOrder': 'rotateOrder',
        'constraintJointOrientX': 'jointOrientX',
        'constraintJointOrientY': 'jointOrientY',
        'constraintJointOrientZ': 'jointOrientZ',
        'scaleCompensate': 'segmentScaleCompensate',
        'inverseScaleX': 'inverseScaleX',
        'inverseScaleY': 'inverseScaleY',
        'inverseScaleZ': 'inverseScaleZ',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }
    __outputs__ = {
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Attributes
    interpType = mpyattribute.MPyAttribute('interpType')  # No flip, average, shortest, longest, cache
    offset = mpyattribute.MPyAttribute('offset')
    offsetX = mpyattribute.MPyAttribute('offsetX')
    offsetY = mpyattribute.MPyAttribute('offsetY')
    offsetZ = mpyattribute.MPyAttribute('offsetZ')
    restRotate = mpyattribute.MPyAttribute('restRotate')
    restRotateX = mpyattribute.MPyAttribute('restRotateX')
    restRotateY = mpyattribute.MPyAttribute('restRotateY')
    restRotateZ = mpyattribute.MPyAttribute('restRotateZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        pass
    # endregion
