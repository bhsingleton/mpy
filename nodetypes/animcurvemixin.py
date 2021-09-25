from maya import cmds as mc
from maya.api import OpenMaya as om

from . import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnimCurveMixin(dependencymixin.DependencyMixin):
    """
    Overload of DependencyMixin class used to interface with animation curves.
    """

    __apitype__ = om.MFn.kAnimCurve

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(AnimCurveMixin, self).__init__(*args, **kwargs)
