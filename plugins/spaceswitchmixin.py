import math

from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import transformutils, plugutils
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

    def addSpace(self, space, **kwargs):
        """
        Adds the supplied spaces to this switch.

        :type space: mpy.builtins.transformmixin.TransformMixin
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

        if space is not None:

            # Connect space to switch
            #
            self.setAttr(f'target[{index}].targetName', space.name())
            self.connectPlugs(space[f'worldMatrix[{space.instanceNumber()}]'], f'target[{index}].targetMatrix')

            if maintainOffset:

                offsetMatrix = restWorldMatrix * space.worldInverseMatrix()
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

    def addSpaces(self, spaces, **kwargs):
        """
        Adds the supplied spaces to this switch.

        :type spaces: List[mpy.builtins.transformmixin.TransformMixin]
        :rtype: List[int]
        """

        numSpaces = len(spaces)
        indices = [None] * numSpaces

        for (i, space) in enumerate(spaces):

            indices[i] = self.addSpace(space, **kwargs)

        return indices
    # endregion
