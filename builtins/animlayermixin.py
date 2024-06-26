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

        return list(map(self.scene.__call__, animutils.getAnimLayerChildren(self.object())))

    def members(self):
        """
        Returns the plug members from this animation layer.

        :rtype: om.MPlugArray
        """

        return animutils.getAnimLayerMembers(self.object())

    def getAssociatedAnimCurve(self, member, create=False):
        """
        Returns the anim-curve associated with the supplied member.

        :type member: om.MPlug
        :type create: bool
        :rtype: mpy.builtins.animcurvemixin.AnimCurveMixin
        """

        return self.scene(animutils.findAnimCurve(member, animLayer=self.object(), create=create))
    # endregion
