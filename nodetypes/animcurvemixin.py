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

    def inputRange(self):
        """
        Returns the input range from this anim curve.

        :rtype: Tuple[int, int]
        """

        inputs = self.inputs()
        numInputs = len(inputs)

        if numInputs > 0:

            return inputs[0], inputs[-1]

        else:

            return None, None

    def remove(self, *args, **kwargs):
        """
        Removes the key at the specified index.

        :type args: Union[int, om.MTime, Tuple[int, int]]
        :key change: oma.MAnimCurveChange
        :rtype: None
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Evaluate argument type
            #
            arg = args[0]

            if isinstance(arg, int):

                # Call parent method
                #
                self.functionSet().remove(arg, **kwargs)

            elif isinstance(arg, om.MTime):

                # Find index at time
                #
                index = self.find(arg)

                if index is not None:

                    self.remove(index)

                else:

                    log.warning('Cannot locate index at frame: %s!' % arg.value)

            else:

                raise TypeError('remove() expects either an int or MTime (%s given)!' % type(arg).__name__)

        elif numArgs == 2:

            # Remove indices within time range
            #
            startTime, endTime = args
            indices = [i for (i, time) in enumerate(self.inputs()) if startTime <= time <= endTime]

            for i in reversed(indices):

                self.remove(i)

        else:

            raise TypeError('remove() expects 1 or 2 arguments (%s given)!' % numArgs)

    def setValue(self, *args, **kwargs):
        """
        Sets the supplied value at either the specified index or time.
        Be sure to enable `convertUnits` for values that are using UI units!

        :type args: Union[Tuple[om.MTime, Any], Tuple[int, Any]]
        :key change: om.MDGModifier
        :key convertUnits: bool
        :rtype: None
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Set value at current time
            #
            time = om.MTime(self.scene.time, unit=om.MTime.uiUnit())
            value = args[0]

            return self.setValue(time, value, **kwargs)

        elif numArgs == 2:

            # Inspect supplied arguments
            #
            index, value = args

            if isinstance(index, om.MTime):

                index = self.insertKey(index)

            # Check if value requires converting to internal units
            #
            convertUnits = kwargs.pop('convertUnits', False)

            if convertUnits:

                value = animutils.uiToInternalUnit(value, self.animCurveType)

            # Update value at index
            #
            self.functionSet().setValue(index, value, **kwargs)

        else:

            raise TypeError('setValue() expects 1-2 arguments (%s given)!' % numArgs)

    def getKeys(self, animationRange=None):
        """
        Returns the keyframes between the specified range.
        If no range is specified then all keyframes are returned instead!

        :type animationRange: Union[Tuple[int, int], None]
        :rtype: List[keyframe.Keyframe]
        """

        # Check if an animation range was requested
        #
        keys = animutils.cacheKeys(self.getAssociatedPlug())

        if not stringutils.isNullOrEmpty(animationRange):

            startTime, endTime = animationRange
            return [key for key in keys if startTime <= key.time <= endTime]

        else:

            return keys

    def replaceKeys(self, keys, animationRange=None, insertAt=None, clear=False):
        """
        Replaces the keys in this animation curve.
        An optional `clear` flag can be specified to remove all existing keys.

        :type keys: List[keyframe.Keyframe]
        :type animationRange: Union[Tuple[int, int], None]
        :type insertAt: Union[int, None]
        :type clear: bool
        :rtype: None
        """

        # Redundancy check
        #
        numKeys = len(keys)

        if numKeys == 0:

            return

        # Check if an animation range was supplied
        #
        startTime, endTime = None, None

        if not stringutils.isNullOrEmpty(animationRange):

            startTime, endTime = animationRange

        else:

            startTime, endTime = keys[0].time, keys[-1].time

        # Check if inputs should be cleared
        #
        if clear:

            self.remove(startTime, endTime)

        # Insert keys
        #
        timeOffset = insertAt - startTime if isinstance(insertAt, (int, float)) else 0

        for key in keys:

            # Add key at time
            #
            time = om.MTime(key.time + timeOffset, unit=om.MTime.uiUnit())
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
            self.remove(startTime, endTime)

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

    def clearKeys(self, **kwargs):
        """
        Removes all keyframes from this curve.
        Once all keys from an animation curve are removed the curve is deleted!

        :key animationRange: Union[Tuple[int, int], None]
        :rtype: None
        """

        # Check if an animation range was supplied
        # If not, then go ahead and delete the curve
        #
        animationRange = kwargs.get('animationRange', None)

        if animationRange is None:

            self.delete()
            return

        # Check if animation range is redundant
        # If so, again, go ahead and delete the curve
        #
        inputRange = self.inputRange()

        if animationRange[0] > inputRange[0] and animationRange[1] < inputRange[1]:

            animutils.clearKeys(self.object(), animationRange=animationRange)

        else:

            self.delete()
    # endregion
