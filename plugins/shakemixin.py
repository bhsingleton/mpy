from maya.api import OpenMaya as om
from .. import mpyattribute
from ..builtins import dependencymixin
from mpy import mpynode
from dcc.maya.libs import plugutils

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

    # region Methods
    def getAssociatedListController(self):
        """
        Returns the list controller associated with this node.

        :rtype: Union[mpy.plugins.listmixin.ListMixin, None]
        """

        plugs = (self['outputTranslate'], self['outputRotate'], self['outputScale'])

        for plug in plugs:

            for child in plugutils.iterChildren(plug):

                destinations = child.destinations()
                destinationCount = len(destinations)

                if destinationCount == 1:

                    return mpynode.MPyNode(destinations[0].node())

                else:

                    continue

        return None
    # endregion
