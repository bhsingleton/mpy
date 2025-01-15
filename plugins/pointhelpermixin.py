import math

from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import locatormixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PointHelperMixin(locatormixin.LocatorMixin):
    """
    Overload of `LocatorMixin` that interfaces with point helper nodes.
    """

    # region Dunderscores
    __plugin__ = 'pointHelper'
    # endregion

    # region Attributes
    centerMarker = mpyattribute.MPyAttribute('centerMarker')
    axisTripod = mpyattribute.MPyAttribute('axisTripod')
    cross = mpyattribute.MPyAttribute('cross')
    square = mpyattribute.MPyAttribute('square')
    box = mpyattribute.MPyAttribute('box')
    pyramid = mpyattribute.MPyAttribute('pyramid')
    diamond = mpyattribute.MPyAttribute('diamond')
    disc = mpyattribute.MPyAttribute('disc')
    arrow = mpyattribute.MPyAttribute('arrow')
    notch = mpyattribute.MPyAttribute('notch')
    tearDrop = mpyattribute.MPyAttribute('tearDrop')
    cylinder = mpyattribute.MPyAttribute('cylinder')
    sphere = mpyattribute.MPyAttribute('sphere')
    custom = mpyattribute.MPyAttribute('custom')
    size = mpyattribute.MPyAttribute('size')
    choice = mpyattribute.MPyAttribute('choice')
    text = mpyattribute.MPyAttribute('text')
    fontSize = mpyattribute.MPyAttribute('fontSize')
    controlPoints = mpyattribute.MPyAttribute('controlPoints')
    fill = mpyattribute.MPyAttribute('fill')
    shaded = mpyattribute.MPyAttribute('shaded')
    drawOnTop = mpyattribute.MPyAttribute('drawOnTop')
    objectMatrix = mpyattribute.MPyAttribute('objectMatrix')
    # endregion

    # region Methods
    def reorientAndScaleToFit(self, *args):
        """
        Locally scales the point helper to fit the distance to the supplied node.

        :type args: Union[mpy.plugins.transformmixin.TransformMixin, None]
        :rtype: None
        """

        # Evaluate supplied target
        #
        siblings = self.parent().siblings()
        numSiblings = len(siblings)
        numArgs = len(args)

        target = args[0] if (numArgs > 0) else siblings[0] if (numSiblings > 0) else None

        if target is None:

            return

        # Get target point
        #
        parentMatrix = self.getAttr(f'parentMatrix[{self.instanceNumber()}]')
        worldMatrix = target.worldMatrix()
        targetMatrix = worldMatrix * parentMatrix.inverse()

        aimVector = om.MVector(transformutils.breakMatrix(targetMatrix)[3])
        distance = aimVector.length()
        size = float(self.size)
        scale = distance / size

        # Compose aim matrix
        #
        forwardVector = aimVector.normal()
        upVector = om.MVector.kZaxisVector

        aimMatrix = transformutils.createAimMatrix(0, forwardVector, 2, upVector)

        # Assign object transform
        #
        localPosition = transformutils.breakMatrix(transformutils.createTranslateMatrix(forwardVector * (distance * 0.5)))[3]
        localRotation = transformutils.decomposeTransformMatrix(aimMatrix)[1]

        self.localPosition = localPosition
        self.localRotate = tuple(map(math.degrees, localRotation))
        self.localScaleX = scale

    def resizeToFitContents(self, size=0.5):
        """
        Local scales the point helper to fit all child nodes.

        :type size: float
        :rtype: None
        """

        # Calculate bounding box
        #
        boundingBox = om.MBoundingBox()

        for descendant in self.parent().iterDescendants(apiType=om.MFn.kTransform):

            shapeBox = descendant.shapeBox()
            shapeBox.transformUsing(descendant.worldMatrix())

            boundingBox.expand(shapeBox)

        boundingBox.transformUsing(self.worldInverseMatrix())

        # Assign bounding transform
        #
        self.size = size
        self.localPosition = boundingBox.center
        self.localRotate = (0.0, 0.0, 0.0)
        self.localScale = (boundingBox.width, boundingBox.height, boundingBox.depth)
    # endregion
