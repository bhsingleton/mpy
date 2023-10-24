from maya.api import OpenMaya as om
from . import deformermixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BlendShapeMixin(deformermixin.DeformerMixin):
    """
    Overload of `DeformerMixin` that interfaces with blendshape deformers.
    """

    # region Dunderscores
    __api_type__ = (om.MFn.kBlendShape, om.MFn.kPluginBlendShape)
    # endregion

    # region Methods
    def addTarget(self, name, target, weight=1.0, index=None):
        """
        Adds the supplied target to this blend shape.

        :type name: str
        :type target: om.MObject
        :type weight: float
        :type index: Union[int, None]
        :rtype: None
        """

        # Evaluate supplied index
        #
        if index is None:

            index = self.targetCount()

        # Update geometry target
        #
        geometryTarget = GeometryTarget(self, index=index)
        geometryTarget.setAlias(name)
        geometryTarget.setWeight(weight)
        geometryTarget.setMeshData(target)

    def removeTarget(self, target):
        """
        Removes the specified target from this blend shape.

        :type target: om.MObject
        :rtype: None
        """

        raise NotImplementedError()

    def iterTargets(self):
        """
        Returns a generator that yields all existing blend shape targets.

        :rtype: iter
        """

        numTargets = self.targetCount()

        for i in range(numTargets):

            yield GeometryTarget(self, index=i)

    def targets(self):
        """
        Returns a list of blend shape targets.

        :rtype: List[GeometryTarget]
        """

        return list(self.iterTargets())

    def targetCount(self):
        """
        Evaluates the total number of active blend shape targets.

        :rtype: int
        """

        return self.findPlug('inputTarget[0].inputTargetGroup').evaluateNumElements()
    # endregion


class GeometryTarget(object):
    """
    Base class used to interface with blend shape targets.
    """

    # region Dunderscores
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
    # endregion

    # region Properties
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
    # endregion

    # region Methods
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

        # Assign alias to plug
        #
        success = self.blendShape.setAlias(alias, plug, replace=True)

        if not success:

            log.warning(
                'Unable to assign "{alias}" alias to "{plugName}" attribute!'.format(
                    alias=alias,
                    plugName=plug.name()
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
        In order to access these please see the following: index = (weight * 1000) + 5000.
        Thus, a weight of 1.0 corresponds to the index 6000.
        By default, we'll leave this at 6000 since Unreal doesn't support in-between targets.

        :type weightIndex: int
        :rtype: om.MObject
        """

        return self.blendShape.findPlug(
            '.inputTarget[{input}].inputTargetGroup[{index}].inputTargetItem[{weightIndex}].inputGeomTarget'.format(
                input=self.input,
                index=self.index,
                weightIndex=weightIndex
            )
        ).asMObject()

    def setMeshData(self, meshData, weightIndex=6000):
        """
        Updates the mesh data associated with this blend shape target.
        Both shape nodes and mesh data objects are supported by this method.

        :type meshData: om.MObject
        :type weightIndex: int
        :rtype: None
        """

        # Get destination plug
        #
        plug = self.blendShape.findPlug(
            '.inputTarget[{input}].inputTargetGroup[{index}].inputTargetItem[{weightIndex}].inputGeomTarget'.format(
                input=self.input,
                index=self.index,
                weightIndex=weightIndex
            )
        )

        # Evaluate object type
        #
        if meshData.hasFn(om.MFn.kMesh):

            mesh = self.blendShape.scene(meshData)
            otherPlug = mesh.findPlug('worldMesh[%s]' % mesh.instanceNumber())

            mesh.connectPlugs(otherPlug, plug, force=True)

        elif meshData.hasFn(om.MFn.kMeshData):

            plug.setMObject(meshData)

        else:

            raise TypeError('setMeshData() expects a valid object (%s given)!' % meshData.apiTypeStr)
    # endregion
