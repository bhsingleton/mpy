from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from . import transformmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class JointMixin(transformmixin.TransformMixin):
    """
    Overload of TransformMixin class used to interface with joint nodes.
    """

    # region Dunderscores
    __apitype__ = om.MFn.kJoint
    # endregion

    # region Attributes
    drawStyle = mpyattribute.MPyAttribute('drawStyle')
    radius = mpyattribute.MPyAttribute('radius')
    stiffness = mpyattribute.MPyAttribute('stiffness')
    stiffnessX = mpyattribute.MPyAttribute('stiffnessX')
    stiffnessY = mpyattribute.MPyAttribute('stiffnessY')
    stiffnessZ = mpyattribute.MPyAttribute('stiffnessZ')
    preferredAngle = mpyattribute.MPyAttribute('preferredAngle')
    preferredAngleX = mpyattribute.MPyAttribute('preferredAngleX')
    preferredAngleY = mpyattribute.MPyAttribute('preferredAngleY')
    preferredAngleZ = mpyattribute.MPyAttribute('preferredAngleZ')
    segmentScaleCompensate = mpyattribute.MPyAttribute('segmentScaleCompensate')
    side = mpyattribute.MPyAttribute('side')
    type = mpyattribute.MPyAttribute('type')
    otherType = mpyattribute.MPyAttribute('otherType')
    drawLabel = mpyattribute.MPyAttribute('drawLabel')
    # endregion

    # region Methods
    def jointOrient(self):
        """
        Returns the joint orient component.

        :rtype: om.MEulerRotation
        """

        return transformutils.getJointOrient(self.dagPath())

    def setJointOrient(self, jointOrient):
        """
        Updates the joint orient component.

        :type jointOrient: om.MEulerRotation
        :rtype: None
        """

        transformutils.setJointOrient(self.dagPath(), jointOrient)

    def resetJointOrient(self):
        """
        Resets the joint orient component.

        :rtype: None
        """

        transformutils.resetJointOrient(self.dagPath())

    def resetTransform(self):
        """
        Resets all of the transform components including joint orient.

        :rtype: None
        """

        # Call parent method
        #
        super(JointMixin, self).resetTransform()

        # Reset joint orient
        #
        self.resetJointOrient()
    # endregion
