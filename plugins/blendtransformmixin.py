from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BlendTransformMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with blend-transform nodes.
    """

    # region Dunderscores
    __plugin__ = 'blendTransform'
    # endregion

    # region Attributes
    blender = mpyattribute.MPyAttribute('blender')
    inTranslate1 = mpyattribute.MPyAttribute('inTranslate1')
    inRotate1 = mpyattribute.MPyAttribute('inRotate1')
    inScale1 = mpyattribute.MPyAttribute('inScale1')
    inTranslate2 = mpyattribute.MPyAttribute('inTranslate2')
    inRotate2 = mpyattribute.MPyAttribute('inRotate2')
    inScale2 = mpyattribute.MPyAttribute('inScale2')
    outTranslate = mpyattribute.MPyAttribute('outTranslate')
    outRotate = mpyattribute.MPyAttribute('outRotate')
    outScale = mpyattribute.MPyAttribute('outScale')
    # endregion
