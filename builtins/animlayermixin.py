from maya.api import OpenMaya as om
from dcc.maya.libs import attributeutils, plugutils, animutils
from . import dependencymixin
from .. import mpyattribute

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnimLayerMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with animation layers.
    """

    # region Attributes
    mute = mpyattribute.MPyAttribute('mute')
    solo = mpyattribute.MPyAttribute('solo')
    lock = mpyattribute.MPyAttribute('lock')
    ghost = mpyattribute.MPyAttribute('ghost')
    ghostColor = mpyattribute.MPyAttribute('ghostColor')
    override = mpyattribute.MPyAttribute('override')
    passthrough = mpyattribute.MPyAttribute('passthrough')
    weight = mpyattribute.MPyAttribute('weight')
    rotationAccumulationMode = mpyattribute.MPyAttribute('rotationAccumulationMode')
    scaleAccumulationMode = mpyattribute.MPyAttribute('scaleAccumulationMode')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kAnimLayer

    # endregion

    # region Methods
    def isTopLevelParent(self):
        """
        Evaluates if this the base animation layer.

        :rtype: bool
        """

        return animutils.isBaseAnimLayer(self.object())

    def parent(self):
        """
        Returns the parent of this animation layer.

        :rtype: AnimLayerMixin
        """

        return self.scene(animutils.getAnimLayerParent(self.object()))

    def children(self):
        """
        Returns the children from this animation layer.

        :rtype: List[AnimLayerMixin]
        """

        return list(map(self.scene, animutils.getAnimLayerChildren(self.object())))

    def members(self):
        """
        Returns the plug members from this animation layer.

        :rtype: om.MPlugArray
        """

        return animutils.getAnimLayerMembers(self.object())

    def getAssociatedAnimCurve(self, member):
        """
        Returns the anim-curve associated with the supplied member.

        :type member: om.MPlug
        :rtype: mpy.builtins.animcurvemixin.AnimCurveMixin
        """

        # Find blend node associated with this layer
        #
        layer = self.object()
        blends = animutils.getMemberBlends(member)

        inputPlug = None

        if self.isTopLevelParent():

            inputPlug = plugutils.findPlug(blends[0], 'inputA')

        else:

            attribute = attributeutils.findAttribute(layer, 'blendNodes')
            animLayers = [plugutils.findConnectedMessage(blend, attribute=attribute).node() for blend in blends]

            index = animLayers.index(layer)
            inputPlug = plugutils.findPlug(blends[index], 'inputB')

        # Check if this is a compound plug
        # If so, then get the corresponding indexed child plug
        #
        if inputPlug.isCompound:

            inputChildren = list(plugutils.iterChildren(inputPlug))
            plugChildren = list(plugutils.iterChildren(member.parent()))
            index = plugChildren.index(member)

            return inputChildren[index]

        else:

            return inputPlug
    # endregion
