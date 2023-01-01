from maya.api import OpenMaya as om
from . import constraintmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PoleVectorConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of ConstraintMixin that interfaces with point constraints.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kPoleVectorConstraint

    __targets__ = {
        'targetTranslateX': 'translateX',
        'targetTranslateY': 'translateY',
        'targetTranslateZ': 'translateZ',
        'targetRotatePivotX': 'rotatePivotX',
        'targetRotatePivotY': 'rotatePivotY',
        'targetRotatePivotZ': 'rotatePivotZ',
        'targetRotateTranslateX': 'rotatePivotTranslateX',
        'targetRotateTranslateY': 'rotatePivotTranslateY',
        'targetRotateTranslateZ': 'rotatePivotTranslateZ',
        'targetParentMatrix': 'parentMatrix'
    }

    __inputs__ = {
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'poleVectorX',
        'constraintTranslateY': 'poleVectorY',
        'constraintTranslateZ': 'poleVectorZ'
    }
    # endregion

    # region Attributes
    offset = mpyattribute.MPyAttribute('offset')
    offsetX = mpyattribute.MPyAttribute('offsetX')
    offsetY = mpyattribute.MPyAttribute('offsetY')
    offsetZ = mpyattribute.MPyAttribute('offsetZ')
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
    # endregion

    # region Methods
    def setConstraintObject(self, constraintObject, **kwargs):
        """
        Updates the constraint object for this instance.

        :type constraintObject: transformmixin.TransformMixin
        :key maintainOffset: bool
        :key skipPoleVectorX: bool
        :key skipPoleVectorY: bool
        :key skipPoleVectorZ: bool
        :rtype: None
        """

        # Call parent method
        #
        super(PoleVectorConstraintMixin, self).setConstraintObject(constraintObject, **kwargs)

        # Connect input attributes
        #
        startJoint = self.nodeManager(constraintObject.getAttr('startJoint'))
        startJoint.connectPlugs('translateX', self['constraintRotatePivotX'])
        startJoint.connectPlugs('translateY', self['constraintRotatePivotY'])
        startJoint.connectPlugs('translateZ', self['constraintRotatePivotZ'])
        startJoint.connectPlugs('parentMatrix[%s]' % startJoint.instanceNumber(), self['pivotSpace'])

    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        raise NotImplementedError()
    # endregion
