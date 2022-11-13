from maya.api import OpenMaya as om
from .. import mpyattribute
from ..nodetypes import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MaxformMixin(transformmixin.TransformMixin):
    """
    Overload of TransformMixin that interfaces with expose transforms.
    """

    # region Dunderscores
    __plugin__ = 'maxform'
    # endregion

    # region Attributes
    transform = mpyattribute.MPyAttribute('transform')
    # endregion

    # region Methods
    def getTMController(self):
        """
        Returns the transform controller for this node.

        :rtype: dependencymixin.DependencyMixin
        """

        # Check for null objects
        #
        controller = self.findPlug('transform').source().node()

        if not controller.isNull():

            return self.pyFactory(controller)

        else:

            return None
    # endregion
