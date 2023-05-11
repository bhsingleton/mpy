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

    def clearKeys(self, animationRange=None):
        """
        Removes all keyframes from this curve.
        Once all keys from an animation curve are removed the curve is deleted!

        :key animationRange: Union[Tuple[int, int], None]
        :rtype: None
        """

        # Check if an animation range was supplied
        # If not, then go ahead and delete the animation curve
        #
        if animationRange is None:

            log.debug('No animation range specified to clear!')
            self.delete()

            return

        # Check if animation range is redundant
        # If so, again, go ahead and delete the animation curve
        #
        startTime, endTime = animationRange
        inputRange = self.inputRange()

        if startTime > inputRange[0] or endTime < inputRange[-1]:

            animutils.clearKeys(self.object(), animationRange=animationRange)

        else:

            self.delete()
    # endregion
