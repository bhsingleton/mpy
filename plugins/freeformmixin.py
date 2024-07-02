import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FreeformMixin(transformmixin.TransformMixin):
    """
    Overload of `TransformMixin` that interfaces with transform w/ pre-rotations.
    """

    # region Dunderscores
    __plugin__ = 'freeform'
    # endregion

    # region Methods
    def preEulerRotation(self):
        """
        Returns the transform's pre-rotation component.

        :rtype: om.MEulerRotation
        """

        return om.MEulerRotation(list(map(math.radians, self.getAttr('rotateAxis'))))

    def setPreEulerRotation(self, eulerRotation):
        """
        Updates the transform's pre-euler rotation component.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        self.setAttr('rotateAxis', eulerRotation, convertUnits=False)

    def detectMirroring(self, normal=om.MVector.kXaxisVector):
        """
        Detects the mirror settings for this transform.
        Unlike the parent method, this overload takes the pre-rotation into consideration.

        :type normal: om.MVector
        :rtype: bool
        """

        # Compare parent matrices for translate settings
        #
        matrix = self.parentMatrix()
        xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)
        mirrorXAxis, mirrorYAxis, mirrorZAxis = [transformutils.mirrorVector(axis, normal=normal) for axis in (xAxis, yAxis, zAxis)]

        otherTransform = self.getOppositeNode()
        otherMatrix = otherTransform.parentMatrix()
        otherXAxis, otherYAxis, otherZAxis, otherPos = transformutils.breakMatrix(otherMatrix, normalize=True)

        mirrorTranslateX = (mirrorXAxis * otherXAxis) < 0.0
        mirrorTranslateY = (mirrorYAxis * otherYAxis) < 0.0
        mirrorTranslateZ = (mirrorZAxis * otherZAxis) < 0.0

        # Compare parent matrices, again, but this time with pre-rotations for rotate settings
        #
        preEulerRotation = self.preEulerRotation()
        matrix = preEulerRotation.asMatrix() * self.parentMatrix()
        xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)
        mirrorXAxis, mirrorYAxis, mirrorZAxis = [transformutils.mirrorVector(axis, normal=normal) for axis in (xAxis, yAxis, zAxis)]

        otherPreEulerRotation = otherTransform.preEulerRotation()
        otherMatrix = otherPreEulerRotation.asMatrix() * otherTransform.parentMatrix()
        otherXAxis, otherYAxis, otherZAxis, otherPos = transformutils.breakMatrix(otherMatrix, normalize=True)

        mirrorRotateX = (mirrorXAxis * otherXAxis) > 0.0
        mirrorRotateY = (mirrorYAxis * otherYAxis) > 0.0
        mirrorRotateZ = (mirrorZAxis * otherZAxis) > 0.0

        # Compose mirror settings and update user properties
        #
        settings = {
            'mirrorTranslateX': mirrorTranslateX,
            'mirrorTranslateY': mirrorTranslateY,
            'mirrorTranslateZ': mirrorTranslateZ,
            'mirrorRotateX': mirrorRotateX,
            'mirrorRotateY': mirrorRotateY,
            'mirrorRotateZ': mirrorRotateZ,
        }

        log.info('Detecting "%s" > "%s" mirror settings: %s' % (self.name(), otherTransform.name(), settings))
        self.userProperties.update(settings)

        return True
    # endregion
