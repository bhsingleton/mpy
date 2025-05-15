from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.generators.inclusiverange import inclusiveRange
from . import shapemixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NurbsCurveMixin(shapemixin.ShapeMixin):
    """
    Overload of `ShapeMixin` that interfaces with nurbs curve nodes.
    """

    # region Dunderscores
    __api_type__ = (om.MFn.kNurbsCurve, om.MFn.kBezierCurve)
    # endregion

    # region Attributes
    alwaysDrawOnTop = mpyattribute.MPyAttribute('alwaysDrawOnTop')
    degree = mpyattribute.MPyAttribute('degree')
    form = mpyattribute.MPyAttribute('form')
    dispCV = mpyattribute.MPyAttribute('dispCV')
    dispCurveEndPoints = mpyattribute.MPyAttribute('dispCurveEndPoints')
    dispEP = mpyattribute.MPyAttribute('dispEP')
    dispGeometry = mpyattribute.MPyAttribute('dispGeometry')
    dispHull = mpyattribute.MPyAttribute('dispHull')
    spans = mpyattribute.MPyAttribute('spans')
    # endregion

    # region Methods
    def controlPoints(self, space=om.MSpace.kObject):
        """
        Returns the control points that make up this nurbs curve.

        :type space: om.MSpace
        :rtype: om.MPointArray
        """

        return self.functionSet().cvPositions(space=space)

    def setControlPoints(self, points, space=om.MSpace.kObject):
        """
        Updates the control points for this nurbs curve.

        :type points: om.MPointArray
        :type space: om.MSpace
        :rtype: None
        """

        functionSet = self.functionSet()  # type: om.MFnNurbsCurve
        functionSet.setCVPositions(points, space=space)
        functionSet.updateCurve()

    def curveBox(self, worldSpace=False):
        """
        Returns the bounding-box for the curve excluding control-points!

        :type worldSpace: bool
        :rtype: om.MBoundingBox
        """

        functionSet = self.functionSet()
        numSpans = int(functionSet.numSpans)

        boundingBox = om.MBoundingBox()

        for i in inclusiveRange(0, numSpans, 0.25):

            point = functionSet.getPointAtParam(i, space=om.MSpace.kObject)
            boundingBox.expand(point)

        if worldSpace:

            boundingBox.transformUsing(self.worldMatrix())

        return boundingBox
    # endregion
