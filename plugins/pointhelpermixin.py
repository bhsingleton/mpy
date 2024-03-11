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

        # Get target point
        #
        numArgs = len(args)
        target = args[0] if (numArgs == 1) else self.parent().child(0)

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
        localRotation = transformutils.decomposeTransformMatrix(aimMatrix)[1]

        self.localPosition = (distance * 0.5, 0.0, 0.0)
        self.localRotate = tuple(map(math.degrees, localRotation))
        self.localScale = (scale, 1.0, 1.0)
    # endregion
