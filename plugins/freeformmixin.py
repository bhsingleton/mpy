from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FreeformMixin(transformmixin.TransformMixin):
    """
    Overload of `TransformMixin` that interfaces with transform w/ pre-rotations.
    """

    # region Dunderscores
    __plugin__ = 'freeform'
    # endregion

    # region Methods
    def preEulerRotation(self):
        """
        Returns the transform's pre-rotation component.

        :rtype: om.MEulerRotation
        """

        return om.MEulerRotation(self.getAttr('rotateAxis', convertUnits=False))

    def setPreEulerRotation(self, eulerRotation):
        """
        Updates the transform's pre-euler rotation component.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        self.setAttr('rotateAxis', eulerRotation, convertUnits=False)
    # endregion
