"""
Skin cluster mixin used to manipulate skin weights directly.
As far as maximum number of influence per-vertex go please see the following:
For SM4 (D3D10) and SM5 (D3D11) the max influence is 8.
For ES2 (Mobile) max influence is 4.
Anything prior to UE4 will also be capped at 4 influences.
"""
import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import skinutils
from dcc.vendor.six import string_types, integer_types
from . import deformermixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SkinMixin(deformermixin.DeformerMixin):
    """
    Overload of `DeformerMixin` that interfaces with skin deformers.
    """

    # region Dunderscores
    __api_type__ = (om.MFn.kSkinClusterFilter, om.MFn.kPluginSkinCluster)

    def __getitem__(self, index):
        """
        Private method that returns the weights for the specified vertex.

        :type index: Union[str, int, list, tuple, set, slice]
        :rtype: dict
        """

        # Check index type
        #
        if isinstance(index, integer_types):

            return dict(skinutils.iterWeights(self.object(), index))

        elif isinstance(index, (list, tuple, set)):

            return dict(skinutils.iterWeightList(self.object(), vertexIndices=index))

        elif isinstance(index, slice):

            return dict(skinutils.iterWeightList(self.object(), vertexIndices=list(range(self.__len__()))[index]))

        elif isinstance(index, string_types):

            return super(SkinMixin, self).__getitem__(index)

        else:

            raise TypeError('__getitem__() expects a str or int (%s given)!' % type(index).__name__)

    def __setitem__(self, index, value):
        """
        Private method that updates the weights for the specified vertex.

        :type index: Union[str, int, slice]
        :type value: dict[int:float]
        :rtype: None
        """

        # Check index type
        #
        if isinstance(index, integer_types):

            skinutils.setWeights(self.object(), index, value)

        elif isinstance(index, slice):

            skinutils.setWeightList(self.object(), value)

        elif isinstance(index, string_types):

            super(SkinMixin, self).__setitem__(index, value)

        else:

            raise TypeError('__setitem__() expects a str or int (%s given)!' % type(index).__name__)

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
    # endregion

    # region Attributes
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
    # endregion

    # region Methods
    def iterInfluences(self, skipNullInfluences=True):
        """
        Returns a generator that yields the influence objects from this skin cluster.

        :type skipNullInfluences: bool
        :rtype: Iterator[int, om.MObject]
        """

        for (influenceId, influenceObject) in skinutils.iterInfluences(self.object(), skipNullInfluences=skipNullInfluences):

            yield influenceId, self.scene(influenceObject)

    def influences(self, skipNullInfluences=True):
        """
        Returns a dictionary of index-influence pairs from this skin cluster.

        :type skipNullInfluences: bool
        :rtype: Dict[int, om.MObject]
        """

        return dict(self.iterInfluences(skipNullInfluences=skipNullInfluences))

    def addInfluence(self, influence, index=None):
        """
        Adds the supplied influence to this skin cluster.

        :type influence: om.MObject
        :type index: int
        :rtype: int
        """

        return skinutils.addInfluence(self.object(), influence, index=index)

    def addInfluences(self, *influences):
        """
        Adds the supplied influences to this skin cluster.

        :type influences: List[om.MObject]
        :rtype: List[int]
        """

        influenceCount = len(influences)
        influenceIds = [None] * influenceCount

        for (i, influence) in enumerate(influences):

            influenceIds[i] = self.addInfluence(influence)

        return influenceIds

    def removeInfluence(self, influenceId):
        """
        Removes the specified influence ID from this skin cluster.

        :type influenceId: int
        :rtype: None
        """

        skinutils.removeInfluence(self.object(), influenceId)

    def rootInfluence(self):
        """
        Returns the root joint from this skin.

        :rtype: Union[mpynode.MPyNode, None]
        """

        # Search for common dag path
        #
        influences = self.influences()
        dagPaths = [influenceObject.fullPathName().replace('|', os.path.sep) for (influenceId, influenceObject) in influences.items()]

        commonPath = os.path.commonpath(dagPaths)

        if stringutils.isNullOrEmpty(commonPath):

            return None

        # Get top-most ancestor
        #
        dagPath = commonPath.replace(os.path.sep, "|")
        joint = self.scene(dagPath)

        ancestors = joint.ancestors(apiType=om.MFn.kJoint, includeSelf=True)

        return ancestors[-1]

    def cacheInfluences(self):
        """
        Caches all influence ID-name pairs within the user properties.

        :rtype: None
        """

        self.userProperties['influences'] = {influenceId: influence.name() for (influenceId, influence) in self.iterInfluences(skipNullInfluences=True)}

    def repairInfluences(self):
        """
        Restores any broken connections using the cached influences from the user properties.

        :rtype: None
        """

        # Iterate through influences
        #
        influences = self.userProperties.get('influences', {})
        numInfluences = len(influences)

        success = [None] * numInfluences

        for (i, (influenceId, influenceName)) in enumerate(influences.items()):

            influence = self.scene.getNodeByName(influenceName)

            if influence is not None:

                log.info(f'Repairing "{influenceName}" influence @ index {influenceId}')
                self.addInfluence(influence.object(), index=int(influenceId))

                success[i] = True

            else:

                log.warning(f'Unable to repair "{influenceName}" influence @ index {influenceId}!')
                success[i] = False

        # Evaluate success
        #
        if all(success) and len(success) > 0:

            del self.userProperties['influences']

    def preBindMatrix(self, influenceId):
        """
        Returns the pre-bind matrix for the specified influence ID.
        Be aware these matrices are the equivalent of a transform's worldInverseMatrix!

        :type influenceId: int
        :rtype: om.MMatrix
        """

        return self.getAttr(f'bindPreMatrix[{influenceId}]')

    def setPreBindMatrix(self, influenceId, preBindMatrix):
        """
        Updates the pre-bind matrix for the specified influence ID.
        Be aware these matrices are the equivalent of a transform's world inverse-matrix!

        :type influenceId: int
        :type preBindMatrix: om.MMatrix
        :rtype: None
        """

        self.setAttr(f'bindPreMatrix[{influenceId}]', preBindMatrix)

    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices for all the associated influences.

        :rtype: None
        """

        for (influenceId, influenceObject) in self.iterInfluences():

            influence = self.scene(influenceObject)
            self.setPreBindMatrix(influenceId, influence.worldInverseMatrix())

    def iterWeightList(self, *args):
        """
        Returns a generator that yields the vertex-weight pairs from this skin cluster.
        An optional list of vertex indices can be supplied to limit the generator.

        :rtype: iter
        """

        return skinutils.iterWeightList(self.object(), vertexIndices=args)

    def weightList(self, *args):
        """
        Returns the vertex-weight pairs from this skin clusters.
        An optional list of vertex indices can be supplied to limit the generator.

        :rtype: Dict[int, Dict[int, float]]
        """

        return dict(self.iterWeightList(*args))

    def setWeightList(self, vertexWeights):
        """
        Updates the vertex-weight pairs for this skin clusters.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        skinutils.setWeightList(self.object(), vertexWeights)

    def clean(self):
        """
        Removes any influences that no longer exist.

        :rtype: None
        """

        for (influenceId, influenceObject) in reversed(list(self.iterInfluences(skipNullInfluences=False))):

            if influenceObject is None:

                log.info(f'Removing null influence @ {self.name()}.matrix[{influenceId}]')
                self.removeInfluence(influenceId)

            else:

                continue
    # endregion
