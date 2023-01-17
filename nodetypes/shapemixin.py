from maya import cmds as mc
from maya.api import OpenMaya as om
from . import dagmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ShapeMixin(dagmixin.DagMixin):
    """
    Overload of `DagMixin` that interfaces with shape nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kShape
    # endregion

    # region Attributes
    lineWidth = mpyattribute.MPyAttribute('lineWidth')
    # endregion

    # region Methods
    def addDeformer(self, typeName):
        """
        Returns a new deformer derived from the supplied type name.
        By default this deformer is inserted at the end of the chain.

        :type typeName: str
        :rtype: mpynode.MPyNode
        """

        try:

            results = mc.deformer(self.fullPathName(), type=typeName)
            return self.scene.getNodeByName(results[-1])

        except RuntimeError as exception:

            log.error(exception)
            return None

    def deformers(self):
        """
        Method used to collect all deformers associated with this shape.

        :rtype: list[mpynode.MPyNode]
        """

        return [x for x in reversed(self.getDeformersByType(om.MFn.kGeometryFilt))]

    def isDeformed(self):
        """
        Method used to check if this shape node is being deformed.

        :rtype: bool
        """

        return len(self.deformers()) > 0

    def getDeformersByType(self, apiType):
        """
        Search method used to find a deformer by a specific type.

        :type apiType: int
        :rtype: list[mpynode.MPyNode]
        """

        return self.dependsOn(apiType)

    def hasDeformer(self, apiType):
        """
        Method used to check if this shape has a specific deformer.

        :type apiType: int
        :rtype: bool
        """

        return len(self.getDeformersByType(apiType)) > 0

    def intermediateObject(self):
        """
        Returns the intermediate object associated with this shape.

        :rtype: mpynode.MPyNode
        """

        # Check if this shape is being deformed
        #
        deformers = self.deformers()
        numDeformers = len(deformers)

        if numDeformers:

            return deformers[0].intermediateObject()

        else:

            return None

    def controlPoints(self):
        """
        Returns the control points that make up this shape node.
        This method should be overloaded for complex shape types.

        :rtype: om.MPointArray
        """

        # Find control points plug
        #
        plug = self.findPlug('controlPoints')
        points = om.MPointArray()

        if plug.isNull:

            return points

        #  Iterate through plug elements
        #
        numElements = plug.numElements()
        points.setLength(numElements)

        for physicalIndex in range(numElements):

            # Select plug element
            #
            element = plug.elementByPhysicalIndex(physicalIndex)

            # Get point from elements
            #
            points[physicalIndex] = om.MPoint(
                [
                    element.child(0).asFloat(),
                    element.child(1).asFloat(),
                    element.child(2).asFloat(),
                    1.0
                ]
            )

        return points

    def numControlPoints(self):
        """
        Returns the number of control points associated with this shape.

        :rtype: int
        """

        return self.findPlug('controlPoints').evaluateNumElements()

    def setControlPoints(self, points):
        """
        Updates the control points for this shape node.

        :type points: om.MPointArray
        :rtype: None
        """

        # Find control points plug
        #
        plug = self.findPlug('controlPoints')

        if plug.isNull:

            return

        #  Iterate through plug elements
        #
        numPoints = len(points)

        for logicalIndex in range(numPoints):

            # Get plug element
            #
            element = plug.elementByLogicalIndex(logicalIndex)

            # Commit point to elements
            #
            point = points[logicalIndex]

            element.child(0).setFloat(point[0])
            element.child(1).setFloat(point[1])
            element.child(2).setFloat(point[2])

    def resetTransform(self):
        """
        Resets the parent transform back to origin while preserving the control points.

        :rtype: None
        """

        # Apply parent matrix to control points
        #
        parent = self.parent()
        matrix = parent.matrix()

        controlPoints = [controlPoint * matrix for controlPoint in self.controlPoints()]
        self.setControlPoints(controlPoints)

        # Reset parent transform
        #
        parent.resetMatrix()
    # endregion
