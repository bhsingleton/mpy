from maya import cmds as mc
from maya.api import OpenMaya as om
from abc import abstractmethod
from dcc.python import stringutils
from dcc.maya.libs import transformutils, plugutils
from . import transformmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ConstraintMixin(transformmixin.TransformMixin):
    """
    Overload of TransformMixin class used to interface with constraints.
    """

    # region Dunderscores
    __apitype__ = (om.MFn.kConstraint, om.MFn.kPluginConstraintNode)
    __targets__ = {}  # destination-source pairs
    __inputs__ = {}  # destination-source pairs
    __outputs__ = {}  # source-destination pairs
    # endregion

    # region Attributes
    enableRestPosition = mpyattribute.MPyAttribute('enableRestPosition')
    lockOutput = mpyattribute.MPyAttribute('lockOutput')
    # endregion

    # region Methods
    def constraintObject(self):
        """
        Returns the object being driven by this constraint node.
        The constraint parent inverse matrix plug is usually the common denominator in all constraint nodes.
        It should be fairly safe to query the connection to find this object.

        :rtype: mpynode.MPyNode
        """

        # Check if plug has a connection
        #
        plug = self.findPlug('constraintParentInverseMatrix')
        source = plug.source()

        if not source.isNull:

            return self.pyFactory(source.node())

        else:

            return None

    def setConstraintObject(self, constraintObject, **kwargs):
        """
        Updates the constraint object for this instance.

        :type constraintObject: transformmixin.TransformMixin
        :key maintainOffset: bool
        :key skipTranslateX: bool
        :key skipTranslateY: bool
        :key skipTranslateZ: bool
        :key skipRotateX: bool
        :key skipRotateY: bool
        :key skipRotateZ: bool
        :key skipScaleX: bool
        :key skipScaleY: bool
        :key skipScaleZ: bool
        :rtype: None
        """

        # Check for redundancy
        #
        if constraintObject == self.constraintObject():

            return

        # Rename constraint and re-parent
        #
        constraintName = '{nodeName}_{typeName}1'.format(nodeName=constraintObject.name(), typeName=self.typeName)
        self.setName(constraintName)

        self.setParent(constraintObject)

        # Update rest matrix
        #
        restMatrix = constraintObject.getAttr('matrix')
        self.setRestMatrix(restMatrix)

        # Connect input attributes
        #
        for (destinationName, sourceName) in self.__inputs__.items():

            # Check if plugs exists
            #
            if not constraintObject.hasAttr(sourceName) or not self.hasAttr(destinationName):

                continue

            # Get associated plugs
            #
            source = constraintObject.findPlug(sourceName)
            destination = self.findPlug(destinationName)

            if source.isArray:

                source.selectAncestorLogicalIndex(constraintObject.instanceNumber())

            # Connect plugs
            #
            self.connectPlugs(source, destination, force=True)

        # Connect output attributes
        #
        for (sourceName, destinationName) in self.__outputs__.items():

            # Check if attribute should be skipped
            #
            key = 'skip{attributeName}'.format(attributeName=stringutils.titleize(destinationName))
            skipAttribute = kwargs.get(key, False)

            if skipAttribute:

                log.info('Skipping constraint attribute: %s' % destinationName)
                continue

            # Get associated plugs
            #
            source = self.findPlug(sourceName)
            destination = constraintObject.findPlug(destinationName)

            # Connect plugs
            #
            self.connectPlugs(source, destination, force=True)

    def targets(self):
        """
        Returns all the available constraint targets.

        :rtype: list[ConstraintTarget]
        """

        return list(self.iterTargets())

    def targetObjects(self):
        """
        Returns all the available constraint target nodes.

        :rtype: list[mpynode.MPyNode]
        """

        return [x.targetObject() for x in self.iterTargets()]

    def iterTargets(self):
        """
        Returns a generator that yields all the available constraint targets.

        :rtype: iter
        """

        # Iterate through target indices
        #
        for i in range(self.targetCount()):

            yield ConstraintTarget(self, index=i)

    def targetCount(self):
        """
        Evaluates the number of active target elements.

        :rtype: int
        """

        return self.findPlug('target').evaluateNumElements()

    def nextAvailableTargetIndex(self):
        """
        Returns the next available target index.

        :rtype: int
        """

        plug = self.findPlug('target')
        return plugutils.getNextAvailableElement(plug)

    def addTarget(self, target, maintainOffset=False):
        """
        Adds a new target to this constraint.

        :type target: mpynode.MPyNode
        :type maintainOffset: bool
        :rtype: int
        """

        # Iterate through required target attributes
        #
        index = self.nextAvailableTargetIndex()

        for (destinationName, sourceName) in self.__targets__.items():

            # Check if attributes exist
            #
            if not target.hasAttr(sourceName) or not self.hasAttr(destinationName):

                continue

            # Find associated plugs
            #
            source = target.findPlug(sourceName)
            destination = self.findPlug('target[%s].%s' % (index, destinationName))

            if source.isArray:

                source.selectAncestorLogicalIndex(target.instanceNumber())

            # Connect plugs
            #
            self.connectPlugs(source, destination)

        # Add target weight attribute
        #
        nodeName = target.displayName()
        attributeName = '{nodeName}W{index}'.format(nodeName=nodeName, index=index)

        attribute = self.addAttr(longName=attributeName, attributeType='float', min=0.0, max=1.0, channelBox=True, keyable=True)

        # Connect target weight attributes
        #
        source = om.MPlug(self.object(), attribute)
        source.setFloat(1.0)  # Don't forget to enable target!
        destination = self.findPlug('target[%s].targetWeight' % index)

        self.connectPlugs(source, destination)

        # Check if offset should be maintained
        #
        if maintainOffset:

            self.maintainOffset()

        return index

    def addTargets(self, targets, maintainOffset=False):
        """
        Adds a list of new targets to this constraint.

        :type targets: list[mpynode.MPyNode]
        :type maintainOffset: bool
        :rtype: int
        """

        for target in targets:

            self.addTarget(target, maintainOffset=maintainOffset)

    @abstractmethod
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        pass

    def removeTarget(self, index):
        """
        Removes the specified target from this constraint.

        :type index: int
        :rtype: None
        """

        # Break connections to target element
        #
        plug = self.findPlug('target')
        plug.selectAncestorLogicalIndex(index)

        for attributeName in self.__targets__.keys():

            child = plug.child(self.attribute(attributeName))
            plugutils.breakConnections(child)

        # Remove custom attribute
        #
        child = plug.child(self.attribute('targetWeight'))
        attribute = child.source().attribute()
        plugutils.breakConnections(child)

        self.removeAttr(attribute)

        # Remove element from array
        #
        plugutils.removeMultiInstances(plug, [index])

    def clearTargets(self):
        """
        Removes all the targets from this constraint.

        :rtype: None
        """

        for i in reversed(range(self.targetCount())):

            self.removeTarget(i)

    def restMatrix(self):
        """
        Computes a transform matrix based off the rest components.

        :rtype: om.MMatrix
        """

        # Check if constraint has rest translate
        #
        translateMatrix = om.MMatrix.kIdentity

        if self.hasAttr('restTranslate'):

            translateMatrix = transformutils.createTranslateMatrix(self.getAttr('restTranslate'))

        # Check if constraint has rest rotate
        #
        rotateMatrix = om.MMatrix.kIdentity

        if self.hasAttr('restRotate'):

            rotateMatrix = transformutils.createRotationMatrix(self.getAttr('restRotate'))

        # Check if constraint has rest scale
        #
        scaleMatrix = om.MMatrix.kIdentity

        if self.hasAttr('restScale'):

            scaleMatrix = transformutils.createScaleMatrix(self.getAttr('restScale'))

        # Compose rest matrix
        #
        return scaleMatrix * rotateMatrix * translateMatrix

    def setRestMatrix(self, restMatrix):
        """
        Updates the rest matrix for this constraint by changing the rest components.

        :type restMatrix: om.MMatrix
        :rtype: None
        """

        # Decompose rest matrix
        #
        translate, rotate, scale = transformutils.decomposeTransformMatrix(restMatrix)

        # Check if constraint has rest translate
        #
        if self.hasAttr('restTranslate'):

            self.setAttr('restTranslate', translate)

        # Check if constraint has rest rotate
        #
        if self.hasAttr('restRotate') and self.hasAttr('constraintRotateOrder'):

            rotateOrder = self.getAttr('constraintRotateOrder')
            rotate.reorderIt(rotateOrder)

            self.setAttr('restRotate', rotate)

        # Check if constraint has rest scale
        #
        if self.hasAttr('restScale'):

            self.setAttr('restScale', scale)

    def restInverseMatrix(self):
        """
        Retrieves the inverse rest matrix.

        :rtype: om.MMatrix
        """

        return self.restMatrix().inverse()

    def worldRestMatrix(self):
        """
        Computes the world rest matrix for this constraint.

        :rtype: om.MMatrix
        """

        return self.restMatrix() * self.exclusiveMatrix()

    def worldRestInverseMatrix(self):
        """
        Retrieves the inverse world rest matrix for this constraint.

        :rtype: om.MMatrix
        """

        return self.worldRestMatrix().inverse()
    # endregion


class ConstraintTarget(object):
    """
    Base class used to interface with constraint targets.
    """

    # region Dunderscores
    __slots__ = ('_constraint', '_index')

    def __init__(self, constraint, **kwargs):
        """
        Private method called after a new instance has been created.

        :type constraint: ConstraintMixin
        :rtype: None
        """

        # Call parent method
        #
        super(ConstraintTarget, self).__init__()

        # Declare class variables
        #
        self._constraint = constraint.weakReference()
        self._index = kwargs.get('index', 0)
    # endregion

    # region Properties
    @property
    def constraint(self):
        """
        Getter method used to retrieve the associated constraint for this target.

        :rtype: ConstraintMixin
        """

        return self._constraint()

    @property
    def index(self):
        """
        Getter method used to retrieve the index for this constraint target.

        :rtype: int
        """

        return self._index
    # endregion

    # region Methods
    def targetPlug(self):
        """
        Returns the element associated with this constraint target.

        :rtype: om.MPlug
        """

        return self.constraint.findPlug('target[{index}]'.format(index=self.index))

    def targetChildPlug(self, name):
        """
        Search method used to locate the child plug derived from this constraint target.

        :type name: str
        :rtype: om.MPlug
        """

        return self.targetPlug().child(self.constraint.attribute(name))

    def name(self):
        """
        Returns the alias name for this constraint target.

        :rtype: str
        """

        return self.targetChildPlug('targetWeight').source().partialName(useLongNames=True)

    def setName(self, name):
        """
        Method used to change the alias name on the indexed weight attribute.

        :type name: str
        :rtype: bool
        """

        # Get source connection from target weight plug
        #
        plug = self.targetChildPlug('targetWeight')
        otherPlug = plug.source()

        if otherPlug.isNull:

            return

        # Rename user attribute
        #
        fullPathName = self.constraint.fullPathName()
        fnAttribute = om.MFnAttribute(otherPlug.attribute())

        mc.renameAttr('%s.%s' % (fullPathName, fnAttribute.shortName), name)
        mc.renameAttr('%s.%s' % (fullPathName, fnAttribute.name), name)

    def weight(self):
        """
        Returns the weight for this constraint target.

        :rtype: float
        """

        return self.targetChildPlug('targetWeight').asFloat()

    def targetObject(self):
        """
        Retrieves the target object driving this constraint channel.
        If no source connection is found then none will be returned!

        :rtype: mpynode.MPyNode
        """

        plug = self.targetChildPlug('targetParentMatrix')
        source = plug.source()

        if not source.isNull:

            return self.constraint.pyFactory(source.node())

        else:

            return None

    def targetRotateOrder(self):
        """
        Retrieves the rotate order for this constraint target.

        :rtype: int
        """

        return self.targetChildPlug('targetRotateOrder').asInt()

    def targetOffsetTranslate(self):
        """
        Retrieves the offset translation for this constraint target.
        This method is only supported by parent constraints!

        :rtype: om.MVector
        """

        return om.MVector(
            self.targetChildPlug('targetOffsetTranslateX').asFloat(),
            self.targetChildPlug('targetOffsetTranslateY').asFloat(),
            self.targetChildPlug('targetOffsetTranslateZ').asFloat()
        )

    def setTargetOffsetTranslate(self, translation):
        """
        Updates the offset translation for this constraint target.

        :type translation: om.MVector
        :rtype: None
        """

        self.targetChildPlug('targetOffsetTranslateX').setFloat(translation.x)
        self.targetChildPlug('targetOffsetTranslateY').setFloat(translation.y)
        self.targetChildPlug('targetOffsetTranslateZ').setFloat(translation.z)

    def targetOffsetRotate(self):
        """
        Retrieves the offset rotation for this constraint target.
        This method is only supported by parent constraints!

        :rtype: om.MEulerRotation
        """

        return om.MEulerRotation(
            self.targetChildPlug('targetOffsetRotateX').asFloat(),
            self.targetChildPlug('targetOffsetRotateY').asFloat(),
            self.targetChildPlug('targetOffsetRotateZ').asFloat(),
            order=self.targetRotateOrder()
        )

    def setTargetOffsetRotate(self, rotation):
        """
        Updates the offset rotation for this constraint target.

        :type rotation: om.MEulerRotation
        :rtype: None
        """

        # Check if rotation needs reordering
        #
        rotateOrder = self.targetRotateOrder()

        if rotation.order != rotateOrder:

            rotation = rotation.reorder(rotateOrder)

        # Assign rotation to plugs
        #
        self.targetChildPlug('targetOffsetRotateX').setFloat(rotation.x)
        self.targetChildPlug('targetOffsetRotateY').setFloat(rotation.y)
        self.targetChildPlug('targetOffsetRotateZ').setFloat(rotation.z)
    # endregion
