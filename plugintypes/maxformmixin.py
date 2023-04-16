from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..nodetypes import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MaxformMixin(transformmixin.TransformMixin):
    """
    Overload of `TransformMixin` that interfaces with 3ds Max transforms.
    """

    # region Attributes
    preRotate = mpyattribute.MPyAttribute('preRotate')
    preRotateX = mpyattribute.MPyAttribute('preRotateX')
    preRotateY = mpyattribute.MPyAttribute('preRotateY')
    preRotateZ = mpyattribute.MPyAttribute('preRotateZ')
    transform = mpyattribute.MPyAttribute('transform')
    translationPart = mpyattribute.MPyAttribute('translationPart')
    rotationPart = mpyattribute.MPyAttribute('rotationPart')
    scalePart = mpyattribute.MPyAttribute('scalePart')
    # endregion

    # region Dunderscores
    __plugin__ = 'maxform'
    # endregion

    # region Methods
    def preEulerRotation(self):
        """
        Returns the transform's pre-rotation component.

        :rtype: om.MEulerRotation
        """

        xAngle = self.getAttr('preRotateX', convertUnits=False).asRadians()
        yAngle = self.getAttr('preRotateY', convertUnits=False).asRadians()
        zAngle = self.getAttr('preRotateZ', convertUnits=False).asRadians()

        return om.MEulerRotation(xAngle, yAngle, zAngle)

    def freezeTransform(self, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Pushes the transform's local matrix into the associated list controllers.

        :type includeTranslate: bool
        :type includeRotate: bool
        :type includeScale: bool
        :rtype: None
        """

        # Check if translation should be frozen
        #
        prs = self.getTMController()
        positionController = prs.getPositionController()

        matrix = self.matrix(asTransformationMatrix=True)

        if includeTranslate and positionController is not None:

            positionController.setAttr('list[0].position', matrix.translation())

        # Check if rotation should be frozen
        #
        rotationController = prs.getRotationController()

        if includeRotate and rotationController is not None:

            rotationController.setAttr('list[0].rotation', matrix.rotation(asQuaternion=False))

    def getTMController(self):
        """
        Returns the transform controller for this node.

        :rtype: dependencymixin.DependencyMixin
        """

        # Check for null objects
        #
        controller = self.findPlug('transform').source().node()

        if not controller.isNull():

            return self.scene(controller)

        else:

            return None

    def detectMirroring(self):
        """
        Detects the mirror settings for this transform.
        Unlike the parent method, this overload takes the pre-rotation into consideration.

        :rtype: bool
        """

        # Compare parent matrices for translate settings
        # In 3ds Max translation values are still in parent space!
        #
        matrix = self.parentMatrix()
        xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)
        mirrorXAxis, mirrorYAxis, mirrorZAxis = list(map(transformutils.mirrorVector, (xAxis, yAxis, zAxis)))

        otherTransform = self.getOppositeNode()
        otherMatrix = otherTransform.parentMatrix()
        otherXAxis, otherYAxis, otherZAxis, otherPos = transformutils.breakMatrix(otherMatrix, normalize=True)

        mirrorTranslateX = (mirrorXAxis * otherXAxis) < 0.0
        mirrorTranslateY = (mirrorYAxis * otherYAxis) < 0.0
        mirrorTranslateZ = (mirrorZAxis * otherZAxis) < 0.0

        # Compare parent matrices, again, but this time with pre-rotations for rotate settings
        # In 3ds Max rotation values are in pre-rotation space!
        #
        preEulerRotation = self.preEulerRotation()
        matrix = preEulerRotation.asMatrix() * self.parentMatrix()
        xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)
        mirrorXAxis, mirrorYAxis, mirrorZAxis = list(map(transformutils.mirrorVector, (xAxis, yAxis, zAxis)))

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
