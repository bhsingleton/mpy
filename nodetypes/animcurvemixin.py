from maya.api import OpenMaya as om
from dcc.python import stringutils
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

    def inputs(self):
        """
        Returns all the current time inputs.

        :rtype: List[Union[int, float, om.MTime]
        """

        return [self.input(i).value for i in range(self.numKeys)]

    def setValue(self, value, time=None):
        """
        Sets the supplied value at the specified time.

        :type value: Any
        :type time: Union[int, float, om.MTime, None]
        :rtype: None
        """

        # Check if time is valid
        #
        if isinstance(time, (int, float)):

            time = om.MTime(time, unit=om.MTime.uiUnit())

        elif time is None:

            time = om.MTime(self.scene.time, unit=om.MTime.uiUnit())

        else:

            pass

        # Check if index exists for time
        #
        index = self.find(time)

        if index is None:

            index = self.insertKey(time)

        # Update value at index
        #
        self.functionSet().setValue(index, value)

    def getKeys(self, animationRange=None):
        """
        Returns the keyframes between the specified range.
        If no range is specified then all keyframes are returned instead!

        :type animationRange: Union[Tuple[int, int], None]
        :rtype: List[keyframe.Keyframe]
        """

        keys = animutils.cacheKeys(self.getAssociatedPlug())

        if animationRange is not None:

            startTime, endTime = animationRange
            return [key for key in keys if startTime <= key.time <= endTime]

        else:

            return keys

    def replaceKeys(self, keys, clear=False):
        """
        Replaces the keys in this animation curve.
        An optional `clear` flag can be specified to remove all existing keys.

        :type keys: List[keyframe.Keyframe]
        :type clear: bool
        :rtype: None
        """

        # Redundancy check
        #
        numKeys = len(keys)

        if numKeys == 0:

            return

        # Check if keys should be cleared
        #
        if clear:

            # Remove all keys
            #
            self.clearKeys()

        else:

            # Remove inputs to make room for new keys
            #
            inputs = self.inputs()
            startTime, endTime = keys[0].time, keys[-1].time

            indices = [i for (i, time) in enumerate(inputs) if startTime <= time <= endTime]

            for i in reversed(indices):

                self.remove(i)

        # Insert keys
        #
        for key in keys:

            # Add key at time
            #
            time = om.MTime(key.time, unit=om.MTime.uiUnit())
            i = self.addKey(time, key.value, tangentInType=key.inTangentType, tangentOutType=key.outTangentType)

            # Modify tangents
            #
            self.setWeightsLocked(i, False)
            self.setTangentsLocked(i, False)

            self.setTangent(i, key.inTangent.x, key.inTangent.y, True, convertUnits=False)
            self.setTangent(i, key.outTangent.x, key.outTangent.y, False, convertUnits=False)

            # Re-lock tangents
            #
            self.setTangentsLocked(i, True)

    def insertKeys(self, keys, insertAt, replace=False):
        """
        Inserts the supplied keys into this animation curve at the specified time.
        An optional `replace` flag can be specified to overwrite keys rather than moving them.

        :type keys: List[keyframe.Keyframe]
        :type insertAt: Union[int, float, om.MTime, None]
        :type replace: bool
        :rtype: None
        """

        # Redundancy check
        #
        numKeys = len(keys)

        if numKeys == 0:

            return

        # Check if insert time is valid
        #
        if insertAt is None:

            insertAt = self.scene.time

        # Check if existing keys should be moved or replaced
        #
        inputs = self.inputs()
        startTime, endTime = keys[0].time, keys[-1].time

        if replace:

            # Remove inputs to make room for new keys
            #
            startTime, endTime = keys[0].time, keys[-1].time
            indices = [i for (i, time) in enumerate(inputs) if startTime <= time <= endTime]

            for i in reversed(indices):

                self.remove(i)

        else:

            # Move inputs to make room for new keys
            #
            indices = [i for (i, time) in enumerate(inputs) if time >= insertAt]
            numIndices = len(indices)

            if numIndices >= 1:

                startIndex, endIndex = indices[0], indices[-1]
                difference = endTime - startTime

                self.moveKeys(inputs[startIndex], inputs[endIndex], inputs[startIndex] + difference)

        # Insert keys at time
        #
        for key in keys:

            # Add key at time
            #
            time = om.MTime(key.time, unit=om.MTime.uiUnit())
            i = self.addKey(time, key.value, tangentInType=key.inTangentType, tangentOutType=key.outTangentType)

            # Modify tangents
            #
            self.setWeightsLocked(i, False)
            self.setTangentsLocked(i, False)

            self.setTangent(i, key.inTangent.x, key.inTangent.y, True, convertUnits=False)
            self.setTangent(i, key.outTangent.x, key.outTangent.y, False, convertUnits=False)

            # Re-lock tangents
            #
            self.setTangentsLocked(i, True)

    def moveKeys(self, startTime, endTime, moveTo):
        """
        Moves the animation range to the specified time.

        :type startTime: int
        :type endTime: int
        :type moveTo: int
        :rtype: None
        """

        # Collect indices to move
        #
        currentInputs = self.inputs()

        indices = [i for (i, time) in enumerate(currentInputs) if startTime <= time <= endTime]
        numIndices = len(indices)

        if numIndices == 0:

            return

        # Move indices
        #
        startIndex, endIndex = indices[0], indices[-1]
        offset = moveTo - currentInputs[startIndex]

        for index in indices:

            self.setInput(index, currentInputs[index] + offset)

    def mirrorKeys(self, animationRange=None):
        """
        Mirrors the keyframes based on the associated node's mirror settings.

        :type animationRange: Union[Tuple[int, int], None]
        :rtype: None
        """

        # Get associated node
        #
        plug = self.getAssociatedPlug()
        node = self.scene(plug.node())

        keys = self.getKeys(animationRange=animationRange)

        # Check if keys should be mirrored
        #
        plugName = plug.partialName(useLongNames=True)
        mirrorFlag = 'mirror{name}'.format(name=stringutils.pascalize(plugName))

        mirror = node.userProperties.get(mirrorFlag, False)

        for key in keys:

            key.value *= -1.0 if mirror else 1.0
            key.inTangent.y *= -1.0 if mirror else 1.0
            key.outTangent.y *= -1.0 if mirror else 1.0

        return keys

    def clearKeys(self):
        """
        Removes all keyframes from this curve.

        :rtype: None
        """

        animutils.clearKeys(self.object())
    # endregion
