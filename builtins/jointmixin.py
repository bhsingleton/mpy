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
    Overload of `TransformMixin` that interfaces with joint nodes.
    """

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

    # region Dunderscores
    __api_type__ = om.MFn.kJoint
    # endregion

    # region Methods
    def setParent(self, parent, absolute=False):
        """
        Updates the parent for this node.

        :type parent: Union[None, str, om.MObject, DagMixin]
        :type absolute: bool
        :rtype: None
        """

        # Call parent method
        #
        super(JointMixin, self).setParent(parent, absolute=absolute)

        # Check if inverse-scale is required
        #
        parent = self.parent()

        if parent is not None:

            if parent.hasFn(om.MFn.kJoint):

                self.connectPlugs(parent['scale'], 'inverseScale', force=True)

            else:

                log.debug(f'Skipping "{parent.name()}.scale" > "{self.name()}.inverseScale" connection.')

        else:

            self.breakConnections('inverseScale', source=True)
            self.resetAttr('inverseScale')

    def preEulerRotation(self):
        """
        Returns the transform's pre-euler rotation component.

        :rtype: om.MEulerRotation
        """

        return transformutils.getJointOrient(self.dagPath())

    def setPreEulerRotation(self, eulerRotation):
        """
        Updates the transform's pre-euler rotation component.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        transformutils.setJointOrient(self.dagPath(), eulerRotation)

    def resetPreEulerRotation(self):
        """
        Resets the transform's pre-euler rotation component.

        :rtype: None
        """

        transformutils.resetJointOrient(self.dagPath())

    def preferEulerRotation(self, **kwargs):
        """
        Copies the current euler rotation as the preferred rotation.

        :key skipPreferredAngleX: bool
        :key skipPreferredAngleY: bool
        :key skipPreferredAngleZ: bool
        :rtype: None
        """

        skipPreferredAngleX = kwargs.get('skipPreferredAngleX', False)

        if not skipPreferredAngleX:

            self.preferredAngleX = self.getAttr('rotateX')

        skipPreferredAngleY = kwargs.get('skipPreferredAngleY', False)

        if not skipPreferredAngleY:

            self.preferredAngleY = self.getAttr('rotateY')

        skipPreferredAngleZ = kwargs.get('skipPreferredAngleZ', False)

        if not skipPreferredAngleZ:

            self.preferredAngleZ = self.getAttr('rotateZ')
    # endregion
