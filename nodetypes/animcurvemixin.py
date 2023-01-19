from maya.api import OpenMaya as om
from dcc.maya.libs import animutils
from . import dependencymixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnimCurveMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with animation curves.
    """

    # region Attributes
    curveColor = mpyattribute.MPyAttribute('curveColor')
    inStippleRange = mpyattribute.MPyAttribute('inStippleRange')
    outStippleRange = mpyattribute.MPyAttribute('outStippleRange')
    outStippleThreshold = mpyattribute.MPyAttribute('outStippleThreshold')
    postInfinity = mpyattribute.MPyAttribute('postInfinity')
    preInfinity = mpyattribute.MPyAttribute('preInfinity')
    rotationInterpolation = mpyattribute.MPyAttribute('rotationInterpolation')
    stipplePattern = mpyattribute.MPyAttribute('stipplePattern')
    stippleReverse = mpyattribute.MPyAttribute('stippleReverse')
    tangentType = mpyattribute.MPyAttribute('tangentType')
    useCurveColor = mpyattribute.MPyAttribute('useCurveColor')
    weightedTangents = mpyattribute.MPyAttribute('weightedTangents')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kAnimCurve
    # endregion

    # region Methods
    def getAssociatedPlug(self):
        """
        Returns a copy of the keys from this node.

        :rtype: om.MPlug
        """

        plug = self.findPlug('output')

        destinations = plug.destinations()
        numDestinations = len(destinations)

        if numDestinations == 1:

            return destinations[0]

        else:

            return None

    def setValueAtFrame(self, value, frame):
        """
        Sets the supplied value at the specified time.

        :type value: Any
        :type frame: int
        :rtype: None
        """

        # Get index at time
        #
        time = om.MTime(frame, unit=om.MTime.uiUnit())
        index = self.find(time)

        if index is None:

            index = self.insertKey(time)

        # Update value at index
        #
        self.setValue(index, value)

    def cacheKeys(self):
        """
        Caches the keyframes from this curve.

        :rtype: List[keyframe.Keyframe]
        """

        return animutils.cacheKeys(self.getAssociatedPlug())

    def assumeCache(self, cache):
        """
        Assumes the keyframes from the supplied cache.

        :type cache: List[keyframe.Keyframe]
        :rtype: None
        """

        # Clear existing keys
        #
        self.clearKeys()

        # Iterate through cache
        #
        for (i, keyframe) in enumerate(cache):

            # Add key at time
            #
            time = om.MTime(keyframe.time, unit=om.MTime.uiUnit())
            self.addKey(time, keyframe.value, tangentInType=keyframe.inTangentType, tangentOutType=keyframe.outTangentType)

            # Modify tangents
            #
            self.setWeightsLocked(i, False)
            self.setTangentsLocked(i, False)

            self.setTangent(i, keyframe.inTangent[0], keyframe.inTangent[1], True, convertUnits=False)
            self.setTangent(i, keyframe.outTangent[0], keyframe.outTangent[1], False, convertUnits=False)

            # Re-lock tangents
            #
            self.setTangentsLocked(i, True)

    def clearKeys(self):
        """
        Removes all keyframes from this curve.

        :rtype: None
        """

        animutils.clearKeys(self.object())
    # endregion
