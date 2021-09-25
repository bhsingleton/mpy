"""
Skin cluster mixin used to manipulate skin weights directly.
As far as maximum number of influence per-vertex go please see the following:
For SM4 (D3D10) and SM5 (D3D11) the max influence is 8.
For ES2 (Mobile) max influence is 4.
Anything prior to UE4 will also be capped at 4 influences.
"""
from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import skinutils

from . import deformermixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SkinMixin(deformermixin.DeformerMixin):
    """
    Overload of DeformerMixin used to interface with skin cluster nodes.
    """

    __apitype__ = (om.MFn.kSkinClusterFilter, om.MFn.kPluginSkinCluster)

    skinningMethod = mpyattribute.MPyAttribute('skinningMethod')
    normalizeWeights = mpyattribute.MPyAttribute('normalizeWeights')
    maxInfluences = mpyattribute.MPyAttribute('maxInfluences')
    maintainMaxInfluences = mpyattribute.MPyAttribute('maintainMaxInfluences')
    lockWeights = mpyattribute.MPyAttribute('lockWeights')
    dropoffRate = mpyattribute.MPyAttribute('dropoffRate')
    dropoff = mpyattribute.MPyAttribute('dropoff')
    smoothness = mpyattribute.MPyAttribute('smoothness')
    deformUserNormals = mpyattribute.MPyAttribute('deformUserNormals')
    bindPose = mpyattribute.MPyAttribute('bindPose')
    bindVolume = mpyattribute.MPyAttribute('bindVolume')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(SkinMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, index):
        """
        Private method that returns the weights for the specified vertex.

        :type index: Union[int, list, tuple, set, slice]
        :rtype: dict
        """

        # Check index type
        #
        if isinstance(index, int):

            return dict(skinutils.iterWeights(self.object(), index))

        elif isinstance(index, (list, tuple, set)):

            return dict(skinutils.iterWeightList(self.object(), vertexIndices=index))

        elif isinstance(index, slice):

            return dict(skinutils.iterWeightList(self.object(), vertexIndices=list(range(self.__len__()))[index]))

        else:

            raise TypeError('__getitem__() expects an int (%s given)!' % type(index).__name__)

    def __setitem__(self, index, value):
        """
        Private method that updates the weights for the specified vertex.

        :type index: int
        :type value: dict[int:float]
        :rtype: None
        """

        skinutils.setWeights(self.object(), index, value)

    def __iter__(self):
        """
        Private method that returns a generator that yields all of the vertex weights from this skin cluster.

        :rtype: iter
        """

        return self.iterWeightList()

    def __len__(self):
        """
        Private method that evaluates the number of control points affected by this skin cluster.

        :rtype: int
        """

        return skinutils.numControlPoints(self.object())

    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence objects from this skin cluster.

        :rtype: iter
        """

        return skinutils.iterInfluences(self.object())

    def iterWeightList(self, *args):
        """
        Returns a generator that yields all of the vertex weights from this skin cluster.
        An optional list of vertex indices can be supplied to limit the generator.

        :rtype: iter
        """

        return skinutils.iterWeightList(self.object(), vertexIndices=args)
