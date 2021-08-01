import maya.cmds as mc
import maya.api.OpenMaya as om

from . import deformermixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BlendShapeMixin(deformermixin.DeformerMixin):
    """
    Overload of DeformerMixin class used to interface with blendshape nodes.
    """

    __apitype__ = (om.MFn.kBlendShape, om.MFn.kPluginBlendShape)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(BlendShapeMixin, self).__init__(*args, **kwargs)

    def iterTargets(self):
        """
        Returns a generator that yields all of the existing blend shape targets.

        :rtype: iter
        """

        numTargets = self.targetCount()

        for i in range(numTargets):

            yield GeometryTarget(self, index=i)

    def targets(self):
        """
        Returns a list of blend shape targets.

        :rtype: list[GeometryTarget]
        """

        return list(self.iterTargets())

    def targetCount(self):
        """
        Evaluates the total number of active blend shape targets.

        :rtype: int
        """

        return self.findPlug('inputTarget[0].inputTargetGroup').evaluateNumElements()


class GeometryTarget(object):
    """
    Base class used to interface with blend shape targets.
    """

    __slots__ = ('_blendShape', '_input', '_index')

    def __init__(self, blendShape, **kwargs):
        """
        Private method called after a new instance has been created.

        :type blendShape: BlendShapeMixin
        :rtype: None
        """

        # Call parent method
        #
        super(GeometryTarget, self).__init__()

        # Declare class variables
        #
        self._blendShape = blendShape.weakReference()

        self._input = kwargs.get('input', 0)
        self._index = kwargs.get('index', 0)

    @property
    def blendShape(self):
        """
        Getter method used to retrieve the blend shape this geometry target is associated with.

        :rtype: BlendShapeMixin
        """

        return self._blendShape()

    @property
    def input(self):
        """
        Getter method used to retrieve the input index for this geometry target.

        :rtype: int
        """

        return self._input

    @property
    def index(self):
        """
        Getter method used to retrieve the index for this geometry target.

        :rtype: int
        """

        return self._index

    def alias(self):
        """
        Returns the alias name for this geometry target.

        :rtype: str
        """

        return self.blendShape.findPlug('weight[{index}]'.format(index=self.index)).partialName(useAlias=True)

    def setAlias(self, alias):
        """
        Method used to change the alias name on the indexed weight attribute.

        :type alias: str
        :rtype: bool
        """

        # Get weight plug
        #
        plug = self.blendShape.findPlug('weight')
        plug.selectAncestorLogicalIndex(self.index)

        # Get attribute name
        #
        attributeName = plug.partialName(includeNodeName=False, includeInstancedIndices=False, useLongNames=True)

        # Assign alias to plug
        #
        success = self.blendShape.setAlias(alias, attributeName, plug, add=True)

        if not success:

            log.warning(
                'Unable to assign "{alias}" alias to "{nodeName}.{attributeName}" attribute!'.format(
                    alias=alias,
                    nodeName=self.blendShape.name(),
                    attributeName=attributeName
                )
            )

        return success

    def weight(self):
        """
        Returns the weight value for this geometry target.

        :rtype: float
        """

        return self.blendShape.findPlug('weight[{index}]'.format(index=self.index)).asFloat()

    def setWeight(self, weight):
        """
        Updates the weight value for this geometry target.

        :type weight: float
        :rtype: None
        """

        self.blendShape.findPlug('weight[{index}]'.format(index=self.index)).setFloat(weight)

    def weights(self):
        """
        Returns the vertex weights associated with this blend shape target.
        :rtype: dict
        """

        # Iterate through plug elements
        #
        plug = self.blendShape.findPlug(
            '.inputTarget[{input}}].inputTargetGroup[{index}].targetWeights'.format(
                input=self.input,
                index=self.index
            )
        )

        indices = plug.getExistingArrayAttributeIndices()
        weights = {}

        for physicalIndex, logicalIndex in enumerate(indices):

            plug.selectAncestorLogicalIndex(logicalIndex)
            weights[logicalIndex] = plug.asFloat()

        return weights

    def meshData(self, weightIndex=6000):
        """
        Returns the mesh data object associated with this blend shape target.
        Since inbetween targets can be stored the node allows for indexed targets.
        In order to access these please see the following:
            index = wt * 1000 + 5000.
        Thus a weight of 1.0 corresponds to the index 6000.
        By default we'll leave this at 6000 since Unreal doesn't support inbetweens.

        :param weightIndex: int
        :rtype: om.MObject
        """

        return self.blendShape.findPlug(
            '.inputTarget[{input}].inputTargetGroup[{index}].inputTargetItem[{weightIndex}].inputGeomTarget'.format(
                input=self.input,
                index=self.index,
                weightIndex=weightIndex
            )
        ).asMObject()
