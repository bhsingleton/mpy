import math

from maya.api import OpenMaya as om, OpenMayaAnim as oma
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
    preInfinity = mpyattribute.MPyAttribute('preInfinity')
    postInfinity = mpyattribute.MPyAttribute('postInfinity')
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

        return animutils.getInputs(self.object())

    def inputRange(self):
        """
        Returns the input range from this anim curve.

        :rtype: Tuple[int, int]
        """

        return animutils.getInputRange(self.object())

    def remove(self, *args, **kwargs):
        """
        Removes the key at the specified time or index.

        :type args: Union[int, om.MTime, Tuple[int, int]]
        :key change: oma.MAnimCurveChange
        :rtype: None
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            # Get current time
            #
            time = om.MTime(self.scene.time, unit=om.MTime.uiUnit())
            self.remove(time)

        elif numArgs == 1:

            # Evaluate argument type
            #
            arg = args[0]

            if isinstance(arg, int):

                # Call parent method
                #
                self.functionSet().remove(arg, **kwargs)

            elif isinstance(arg, float):

                # Convert to time and process again
                #
                time = om.MTime(arg, unit=om.MTime.uiUnit())
                self.remove(time)

            elif isinstance(arg, om.MTime):

                # Find index at time
                #
                index = self.find(arg)

                if index is not None:

                    self.remove(index)

                else:

                    log.warning(f'Cannot locate index at frame: {arg.value}!' )

            else:

                raise TypeError(f'remove() expects either an int or MTime ({type(arg).__name__} given)!')

        elif numArgs == 2:

            # Remove indices within time range
            #
            startTime, endTime = args
            indices = [i for (i, time) in enumerate(self.inputs()) if startTime <= time <= endTime]

            for i in reversed(indices):

                self.remove(i)

        else:

            raise TypeError(f'remove() expects 1 or 2 arguments ({numArgs} given)!')

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
        keys = animutils.copyKeys(self.getAssociatedPlug())

        if not stringutils.isNullOrEmpty(animationRange):

            startTime, endTime = animationRange
            return [key for key in keys if startTime <= key.time <= endTime]

        else:

            return keys

    def getInfinityKeys(self, animationRange, alignEndTangents=False):
        """
        Returns the infinity keyframes between the specified range.

        :type animationRange: Union[Tuple[int, int], None]
        :type alignEndTangents: bool
        :rtype: List[keyframe.Keyframe]
        """

        # Check if anim-curve has enough inputs
        #
        keyframes = self.getKeys()
        numKeyframes = len(keyframes)

        if not (numKeyframes >= 2):

            return keyframes

        # Calculate number of cycles
        #
        startFrame, endFrame = animationRange

        startInput, endInput = keyframes[0].time, keyframes[-1].time
        inputDifference = (endInput - startInput)

        preCycles = abs(math.floor((startFrame - startInput) / inputDifference))
        postCycles = abs(math.floor((endInput - endFrame) / inputDifference))

        # Iterate through infinity cycles
        #
        startBakeFrame = keyframes[0].time - (preCycles * inputDifference)
        cycles = preCycles + 1 + postCycles
        lastIndex = numKeyframes - 1
        lastCycle = cycles - 1

        infinityKeyframes = []

        for cycle in range(cycles):

            # Iterate through keyframes
            #
            offset = cycle * inputDifference

            for (i, keyframe) in enumerate(keyframes):

                # Check if frame should be skipped
                #
                skipFirstTangent = (i == 0 and not alignEndTangents) and cycle > 0
                skipLastTangent = (i == lastIndex and alignEndTangents) and cycle < lastCycle

                if skipFirstTangent or skipLastTangent:

                    continue

                # Calculate time offset and value
                #
                time = startBakeFrame + (keyframe.time - startInput) + offset
                value = keyframe.value

                if self.postInfinityType != oma.MFnAnimCurve.kCycle:

                    value = self.evaluate(om.MTime(time, unit=om.MTime.uiUnit()))

                # Copy and offset keyframe
                #
                infinityKeyframe = keyframe.copy()
                infinityKeyframe.time = time
                infinityKeyframe.value = value
                infinityKeyframes.append(infinityKeyframe)

        return infinityKeyframes

    def replaceKeys(self, keys, insertAt=None, animationRange=None):
        """
        Replaces the keys in this animation curve.

        :type keys: List[keyframe.Keyframe]
        :type insertAt: Union[int, None]
        :type animationRange: Union[Tuple[int, int], None]
        :rtype: None
        """

        animutils.replaceKeys(self.object(), keys, insertAt=insertAt, animationRange=animationRange)

    def insertKeys(self, keys, insertAt, replace=False):
        """
        Inserts the supplied keys into this animation curve at the specified time.
        An optional `replace` flag can be specified to overwrite keys rather than moving them.

        :type keys: List[keyframe.Keyframe]
        :type insertAt: Union[int, float, om.MTime, None]
        :type replace: bool
        :rtype: None
        """

        animutils.insertKeys(self.object(), keys, insertAt, replace=replace)

    def moveKeys(self, startTime, endTime, moveTo):
        """
        Moves the animation range to the specified time.

        :type startTime: int
        :type endTime: int
        :type moveTo: int
        :rtype: None
        """

        animutils.moveKeys(self.object(), startTime, endTime, moveTo)

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

    def invertKeys(self):
        """
        Inverts the values on this anim-curve.

        :rtype: None
        """

        # Iterate through keys
        #
        for i in range(self.numKeys):

            # Unlock tangents
            #
            self.setWeightsLocked(i, False)
            self.setTangentsLocked(i, False)

            # Modify keyframe
            #
            inTangentX, inTangentY = self.getTangentXY(i, True)
            self.setTangent(i, inTangentX, -inTangentY, True, convertUnits=False)

            value = self.value(i)
            self.setValue(i, -value)

            outTangentX, outTangentY = self.getTangentXY(i, False)
            self.setTangent(i, outTangentX, -outTangentY, False, convertUnits=False)

            # Re-lock tangents
            #
            self.setTangentsLocked(i, True)

    def clearKeys(self, animationRange=None, delete=True):
        """
        Removes all keyframes from this curve.
        Once all keys from an animation curve are removed the curve is deleted!

        :key animationRange: Union[Tuple[int, int], None]
        :key delete: bool
        :rtype: None
        """

        # Check if there are any keys to remove
        #
        inputRange = self.inputRange()
        inputCount = len(inputRange)

        if inputCount == 0:

            return

        # Check if animation range is redundant
        # If so, go ahead and delete the animation curve
        #
        startTime, endTime = self.scene.animationRange if stringutils.isNullOrEmpty(animationRange) else animationRange
        firstFrame, lastFrame = inputRange[0], inputRange[-1]

        requiresDeleting = (startTime <= firstFrame and endTime >= lastFrame) and delete

        if requiresDeleting:

            self.delete()

        else:

            animutils.clearKeys(self.object(), animationRange=animationRange)
    # endregion
