from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils

from . import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class JointMixin(transformmixin.TransformMixin):
    """
    Overload of TransformMixin class used to interface with joint nodes.
    """

    __apitype__ = om.MFn.kJoint

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(JointMixin, self).__init__(*args, **kwargs)

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
