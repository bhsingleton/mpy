from maya.api import OpenMaya as om
from .. import mpyattribute
from ..nodetypes import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ShakeMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with shake nodes.
    """

    # region Attributes
    envelope = mpyattribute.MPyAttribute('envelope')
    seed = mpyattribute.MPyAttribute('seed')
    frequency = mpyattribute.MPyAttribute('frequency')
    fractal = mpyattribute.MPyAttribute('fractal')
    roughness = mpyattribute.MPyAttribute('roughness')
    rampIn = mpyattribute.MPyAttribute('rampIn')
    rampOut = mpyattribute.MPyAttribute('rampOut')
    strength = mpyattribute.MPyAttribute('strength')
    strengthX = mpyattribute.MPyAttribute('strengthX')
    strengthY = mpyattribute.MPyAttribute('strengthY')
    strengthZ = mpyattribute.MPyAttribute('strengthZ')
    positive = mpyattribute.MPyAttribute('positive')
    positiveX = mpyattribute.MPyAttribute('positiveX')
    positiveY = mpyattribute.MPyAttribute('positiveY')
    positiveZ = mpyattribute.MPyAttribute('positiveZ')
    # endregion

    # region Dunderscores
    __plugin__ = 'shake'
    # endregion
