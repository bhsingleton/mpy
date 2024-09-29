import math

from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import transformutils, plugutils, plugmutators
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SpaceSwitchMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with space-switch nodes.
    """

    # region Dunderscores
    __plugin__ = 'spaceSwitch'
    # endregion

    # region Attributes
    envelope = mpyattribute.MPyAttribute('envelope')
    positionSpace = mpyattribute.MPyAttribute('positionSpace')
    rotationSpace = mpyattribute.MPyAttribute('rotationSpace')
    scaleSpace = mpyattribute.MPyAttribute('scaleSpace')
    weighted = mpyattribute.MPyAttribute('weighted')
    rotateOrder = mpyattribute.MPyAttribute('rotateOrder')
    restMatrix = mpyattribute.MPyAttribute('restMatrix')
    parentInverseMatrix = mpyattribute.MPyAttribute('parentInverseMatrix')
    # endregion

    # region Methods
    def driven(self):
        """
        Returns the node driven by this space switch.

        :rtype: mpy.builtins.transformmixin.TransformMixin
        """

        plug = self.findPlug('parentInverseMatrix')
        source = plug.source()

        if not source.isNull:

            return self.scene(source.node())

        else:

            return None

    def setDriven(self, driven, **kwargs):
        """
        Updates the node driven by this space switch.

        :type driven: mpy.builtins.transformmixin.TransformMixin
        :rtype: None
        """

        # Connect plugs
        #
        self.setAttr('restMatrix', driven.matrix(asTransformationMatrix=True))
        self.connectPlugs(driven['rotateOrder'], 'rotateOrder')
        self.connectPlugs(driven[f'parentInverseMatrix[{driven.instanceNumber()}]'], 'parentInverseMatrix')

        # Connect translate attributes
        #
        skipTranslate = kwargs.get('skipTranslate', False)

        if not skipTranslate:

            sources = list(plugutils.iterChildren(self['outputTranslate']))
            destinations = list(plugutils.iterChildren(driven['translate']))

            for (source, destination) in zip(sources, destinations):

                attributeName = destination.partialName(useLongNames=True)
                key = 'skip{attributeName}'.format(attributeName=stringutils.pascalize(attributeName))
                skipChild = kwargs.get(key, skipTranslate)

                if not skipChild:

                    self.connectPlugs(source, destination)

        # Connect rotate attributes
        #
        skipRotate = kwargs.get('skipRotate', False)

        if not skipRotate:

            sources = list(plugutils.iterChildren(self['outputRotate']))
            destinations = list(plugutils.iterChildren(driven['rotate']))

            for (source, destination) in zip(sources, destinations):

                attributeName = destination.partialName(useLongNames=True)
                key = 'skip{attributeName}'.format(attributeName=stringutils.pascalize(attributeName))
                skipChild = kwargs.get(key, skipRotate)

                if not skipChild:

                    self.connectPlugs(source, destination)

        # Connect scale attributes
        #
        skipScale = kwargs.get('skipScale', False)

        if not skipScale:

            sources = list(plugutils.iterChildren(self['outputScale']))
            destinations = list(plugutils.iterChildren(driven['scale']))

            for (source, destination) in zip(sources, destinations):

                attributeName = destination.partialName(useLongNames=True)
                key = 'skip{attributeName}'.format(attributeName=stringutils.pascalize(attributeName))
                skipChild = kwargs.get(key, skipScale)

                if not skipChild:

                    self.connectPlugs(source, destination)

    def targetCount(self):
        """
        Evaluates the number of active target elements.

        :rtype: int
        """

        return self.findPlug('target').evaluateNumElements()

    def targets(self):
        """
        Returns all the available constraint targets.

        :rtype: List[SpaceTarget]
        """

        return list(self.iterTargets())

    def iterTargets(self):
        """
        Returns a generator that yields all the available constraint targets.

        :rtype: Iterator[SpaceTarget]
        """

        # Iterate through target indices
        #
        for physicalIndex in range(self.targetCount()):

            plug = self.findPlug(f'target').elementByPhysicalIndex(physicalIndex)
            logicalIndex = plug.logicalIndex()

            yield SpaceTarget(self, index=logicalIndex)

    def addTarget(self, target, **kwargs):
        """
        Adds the supplied spaces to this switch.

        :type target: mpy.builtins.transformmixin.TransformMixin
        :key maintainOffset: bool
        :rtype: int
        """

        # Get world rest-matrix
        #
        driven = self.driven()
        restMatrix = om.MMatrix(self.restMatrix)

        restWorldMatrix = restMatrix * driven.parentMatrix()

        # Get next available space index
        #
        plug = self.findPlug('target')
        attribute = self.attribute('targetMatrix')
        index = self.getNextAvailableConnection(plug, child=attribute)

        maintainOffset = kwargs.get('maintainOffset', True)

        if target is not None:

            # Connect space to switch
            #
            self.setAttr(f'target[{index}].targetName', target.name())
            self.connectPlugs(target[f'worldMatrix[{target.instanceNumber()}]'], f'target[{index}].targetMatrix')

            if maintainOffset:

                offsetMatrix = restWorldMatrix * target.worldInverseMatrix()
                offsetTranslate, offsetRotate, offsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)

                self.setAttr(f'target[{index}].targetOffsetTranslate', offsetTranslate)
                self.setAttr(f'target[{index}].targetOffsetRotate', list(map(math.degrees, offsetRotate)))
                self.setAttr(f'target[{index}].targetOffsetScale', offsetScale)

        else:

            # Add world space to switch
            #
            worldMatrix = om.MMatrix.kIdentity

            self.setAttr(f'target[{index}].targetName', 'World')
            self.setAttr(f'target[{index}].targetMatrix', worldMatrix)

            if maintainOffset:

                offsetMatrix = restWorldMatrix * worldMatrix.inverse()
                offsetTranslate, offsetRotate, offsetScale = transformutils.decomposeTransformMatrix(offsetMatrix)

                self.setAttr(f'target[{index}].targetOffsetTranslate', offsetTranslate)
                self.setAttr(f'target[{index}].targetOffsetRotate', list(map(math.degrees, offsetRotate)))
                self.setAttr(f'target[{index}].targetOffsetScale', offsetScale)

        return index

    def addTargets(self, targets, **kwargs):
        """
        Adds the supplied spaces to this switch.

        :type targets: List[mpy.builtins.transformmixin.TransformMixin]
        :rtype: List[int]
        """

        numTargets = len(targets)
        indices = [None] * numTargets

        for (i, target) in enumerate(targets):

            indices[i] = self.addTarget(target, **kwargs)

        return indices
    # endregion


class SpaceTarget(object):
    """
    Base class used to interface with constraint targets.
    """

    # region Dunderscores
    __slots__ = ('_spaceSwitch', '_index')

    def __init__(self, spaceSwitch, **kwargs):
        """
        Private method called after a new instance has been created.

        :type spaceSwitch: SpaceSwitchMixin
        :key index: int
        :rtype: None
        """

        # Call parent method
        #
        super(SpaceTarget, self).__init__()

        # Declare class variables
        #
        self._spaceSwitch = spaceSwitch.weakReference()
        self._index = kwargs.get('index', 0)
    # endregion

    # region Properties
    @property
    def spaceSwitch(self):
        """
        Getter method used to retrieve the associated space-switch for this target.

        :rtype: SpaceSwitchMixin
        """

        return self._spaceSwitch()

    @property
    def index(self):
        """
        Getter method used to retrieve the index for this constraint target.

        :rtype: int
        """

        return self._index
    # endregion

    # region Methods
    def plug(self, *args):
        """
        Returns the plug element associated with this constraint target.

        :type args: Union[str, List[str]]
        :rtype: om.MPlug
        """

        numArgs = len(args)

        if numArgs == 0:

            return self.spaceSwitch.findPlug('target[{index}]'.format(index=self.index))

        elif numArgs == 1:

            return self.plug().child(self.spaceSwitch.attribute(args[0]))

        else:

            raise TypeError(f'plug() expects 1 argument ({numArgs} given)!')

    def name(self):
        """
        Returns the name for this space target.

        :rtype: str
        """

        plug = self.plug('targetName')
        return plugmutators.getValue(plug)

    def setName(self, name):
        """
        Updates the name for this space target.

        :type name: str
        :rtype: None
        """

        plug = self.plug('targetName')
        plugmutators.setValue(plug, name)

    def weight(self):
        """
        Returns the weight for this space target.

        :rtype: Tuple[float, float, float]
        """

        plug = self.plug('targetWeight')
        return plugmutators.getValue(plug)

    def setWeight(self, weight):
        """
        Updates the weight for this space target.

        :type weight: Tuple[float, float, float]
        :rtype: None
        """

        plug = self.plug('targetWeight')
        plugmutators.setValue(plug, weight)
    # endregion
