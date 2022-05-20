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
