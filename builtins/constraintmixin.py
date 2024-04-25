import math

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
    Overload of `TransformMixin` that interfaces with constraint nodes.
    """

    # region Dunderscores
    __api_type__ = (om.MFn.kConstraint, om.MFn.kPluginConstraintNode)
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
        In most cases this returns the immediate parent node.

        :rtype: mpynode.MPyNode
        """

        return self.parent()

    def setConstraintObject(self, constraintObject, **kwargs):
        """
        Updates the constraint object for this instance.

        :type constraintObject: transformmixin.TransformMixin
        :key enableRestPosition: bool
        :rtype: None
        """

        # Redundancy check
        #
        if constraintObject == self.constraintObject():

            return

        # Rename constraint and re-parent
        #
        nodeName = constraintObject.name()
        constraintName = '{nodeName}_{typeName}1'.format(nodeName=nodeName, typeName=self.typeName)
        
        self.setName(constraintName)
        self.setParent(constraintObject)

        # Update rest matrix
        #
        enableRestPosition = kwargs.get('enableRestPosition', True)

        if enableRestPosition:

            restMatrix = kwargs.get('restMatrix', constraintObject.matrix())
            self.setRestMatrix(restMatrix)

            self.enableRestPosition = enableRestPosition

        # Connect input attributes
        #
        inputs = kwargs.get('inputs', self.__inputs__)

        for (destinationName, sourceName) in inputs.items():

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
        skipAll = kwargs.get('skipAll', False)
        outputs = kwargs.get('outputs', self.__outputs__)

        for (sourceName, destinationName) in outputs.items():

            # Check if children should be skipped
            #
            isCartesian = any([destinationName.endswith(axis) for axis in ('X', 'Y', 'Z')])
            parentKey = 'skip{attributeName}'.format(attributeName=stringutils.pascalize(destinationName[:-1])) if isCartesian else destinationName
            skipChildren = kwargs.get(parentKey, skipAll)

            if isCartesian and skipChildren:

                log.debug(f'Skipping "{constraintName}.{sourceName}" > "{nodeName}.{destinationName}" constraint!')
                continue

            # Check if attribute should be skipped
            #
            key = 'skip{attributeName}'.format(attributeName=stringutils.pascalize(destinationName))
            skipAttribute = kwargs.get(key, skipAll)

            if skipAttribute:

                log.debug(f'Skipping "{constraintName}.{sourceName}" > "{nodeName}.{destinationName}" constraint!')
                continue

            # Get associated plugs
            #
            source = self.findPlug(sourceName)
            destination = constraintObject.findPlug(destinationName)

            # Connect plugs
            #
            self.connectPlugs(source, destination)

    def targets(self):
        """
        Returns all the available constraint targets.

        :rtype: List[ConstraintTarget]
        """

        return list(self.iterTargets())

    def targetObjects(self):
        """
        Returns all the available constraint target nodes.

        :rtype: List[transformmixin.TransformMixin]
        """

        return [target.targetObject() for target in self.iterTargets()]

    def iterTargets(self):
        """
        Returns a generator that yields all the available constraint targets.

        :rtype: Iterator[ConstraintTarget]
        """

        # Iterate through target indices
        #
        for physicalIndex in range(self.targetCount()):

            plug = self.findPlug(f'target').elementByPhysicalIndex(physicalIndex)
            logicalIndex = plug.logicalIndex()

            yield ConstraintTarget(self, index=logicalIndex)

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

    def addTarget(self, target, weight=1.0, maintainOffset=False, **kwargs):
        """
        Adds a new target to this constraint.

        :type target: transformmixin.TransformMixin
        :type weight: float
        :type maintainOffset: bool
        :rtype: int
        """

        # Iterate through required target attributes
        #
        target = self.scene(target)
        index = self.nextAvailableTargetIndex()

        connections = kwargs.get('connections', self.__targets__)

        for (destinationName, sourceName) in connections.items():

            # Check if attributes exist
            #
            if not target.hasAttr(sourceName) or not self.hasAttr(destinationName):

                continue

            # Find associated plugs
            #
            source = target.findPlug(sourceName)
            destination = self.findPlug(f'target[{index}].{destinationName}')

            if source.isArray:

                source.selectAncestorLogicalIndex(target.instanceNumber())  # Should be relatively safe?

            # Connect plugs
            #
            self.connectPlugs(source, destination)

        # Add target weight attribute
        #
        attributeName = '{nodeName}W{index}'.format(nodeName=target.name(), index=index)

        attribute = self.addAttr(
            longName=attributeName,
            attributeType='double',
            min=0.0,
            default=1.0,
            keyable=True,
            cachedInternally=True,
            disconnectBehaviour=0
        )

        # Connect target weight attributes
        #
        source = self.findPlug(attribute)
        self.setAttr(source, weight)

        destination = self.findPlug(f'target[{index}].targetWeight')
        self.connectPlugs(source, destination)

        # Check if offset should be maintained
        #
        if maintainOffset:

            self.maintainOffset()

        return index

    def addTargets(self, targets, **kwargs):
        """
        Adds a list of new targets to this constraint.

        :type targets: List[transformmixin.TransformMixin]
        :key maintainOffset: bool
        :rtype: int
        """

        targetCount = len(targets)
        indices = [None] * targetCount

        for (i, target) in enumerate(targets):

            indices[i] = self.addTarget(target, **kwargs)

        return indices

    @abstractmethod
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        pass

    def removeTarget(self, index, maintainOffset=False):
        """
        Removes the specified target from this constraint.

        :type index: int
        :type maintainOffset: bool
        :rtype: None
        """

        # Check if target exists
        #
        targetPlug = self.findPlug('target')
        existingIndices = targetPlug.getExistingArrayAttributeIndices()

        if index not in existingIndices:

            log.warning(f'Cannot locate target @ {index}')
            return

        # Break all connections to target element
        #
        target = ConstraintTarget(self, index=index)
        driver = target.driver()
        element = target.plug()

        self.breakConnections(element, source=True, destination=True, recursive=True)
        self.removePlugElements(targetPlug, [index])

        # Remove associated attribute
        #
        if not driver.isNull:

            self.removeAttr(driver.attribute())

        # Check if offset should be maintained
        #
        if maintainOffset:

            self.maintainOffset()

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

            restTranslate = self.getAttr('restTranslate')
            translateMatrix = transformutils.createTranslateMatrix(restTranslate)

        # Check if constraint has rest rotate
        #
        rotateMatrix = om.MMatrix.kIdentity

        if self.hasAttr('restRotate'):

            restAngles = list(map(math.radians, self.getAttr('restRotate')))
            restOrder = self.getAttr('constraintRotateOrder')
            restEulerRotation = om.MEulerRotation(restAngles, order=restOrder)

            rotateMatrix = restEulerRotation.asMatrix()

        # Check if constraint has rest scale
        #
        scaleMatrix = om.MMatrix.kIdentity

        if self.hasAttr('restScale'):

            restScale = self.getAttr('restScale')
            scaleMatrix = transformutils.createScaleMatrix(restScale)

        # Compose rest matrix
        #
        return scaleMatrix * rotateMatrix * translateMatrix

    def setRestMatrix(self, restMatrix):
        """
        Updates the rest matrix for this constraint.

        :type restMatrix: om.MMatrix
        :rtype: None
        """

        # Decompose rest matrix
        #
        translate, eulerRotation, scale = transformutils.decomposeTransformMatrix(restMatrix)

        # Check if constraint has rest translate
        #
        if self.hasAttr('restTranslate'):

            self.setAttr('restTranslate', translate)

        # Check if constraint has rest rotate
        #
        if self.hasAttr('restRotate'):

            rotateOrder = self.getAttr('constraintRotateOrder')
            eulerRotation.reorderIt(rotateOrder)

            self.setAttr('restRotate', eulerRotation, convertUnits=False)

        # Check if constraint has rest scale
        #
        if self.hasAttr('restScale'):

            self.setAttr('restScale', scale)

    def updateRestMatrix(self):
        """
        Updates the rest matrix for this constraint using the constraint object's transform.

        :rtype: None
        """

        node = self.constraintObject()
        matrix = node.matrix()

        self.setRestMatrix(matrix)

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

        parentInverseMatrix = self.tryGetAttr('constraintParentInverseMatrix', default=om.MMatrix.kIdentity)
        restMatrix = self.restMatrix()

        return restMatrix * parentInverseMatrix.inverse()

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
        :key index: int
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
    def plug(self, *args):
        """
        Returns the plug element associated with this constraint target.

        :type args: Union[str, List[str]]
        :rtype: om.MPlug
        """

        numArgs = len(args)

        if numArgs == 0:

            return self.constraint.findPlug('target[{index}]'.format(index=self.index))

        elif numArgs == 1:

            return self.plug().child(self.constraint.attribute(args[0]))

        else:

            raise TypeError(f'plug() expects 1 argument ({numArgs} given)!')

    def driver(self):
        """
        Returns the driver plug for this constraint target.

        :rtype: om.MPlug
        """

        return self.plug('targetWeight').source()

    def name(self):
        """
        Returns the alias for this constraint target.

        :rtype: str
        """

        plug = self.driver()

        if not plug.isNull:

            return plug.partialName(useLongNames=True)

        else:

            return ''

    def setName(self, name):
        """
        Updates the alias for this constraint target.

        :type name: str
        :rtype: None
        """

        # Get source connection from target weight plug
        #
        plug = self.plug('targetWeight')

        if not plug.isDestination:

            return

        # Rename user attribute
        #
        currentName = self.name()

        if name != currentName:

            fullPathName = self.constraint.fullPathName()
            fnAttribute = om.MFnAttribute(plug.source().attribute())

            mc.renameAttr(f'{fullPathName}.{fnAttribute.name}', name)

    def resetName(self):
        """
        Resets the alias for this constraint target.

        :rtype: None
        """

        # Get source connection from target weight plug
        #
        plug = self.plug('targetWeight')
        otherPlug = plug.source()

        if otherPlug.isNull:

            return

        # Update attribute name using source name
        #
        target = self.targetObject()
        name = f'{target.name()}W{self.index}'

        self.setName(name)

    def weight(self):
        """
        Returns the weight for this constraint target.

        :rtype: float
        """

        return self.plug('targetWeight').asFloat()

    def setWeight(self, weight):
        """
        Updates the weight for this constraint target.

        :type weight: float
        :rtype: None
        """

        self.plug('targetWeight').source().setFloat(weight)

    def targetObject(self):
        """
        Returns the target object driving this constraint channel.
        If no source connection is found then none will be returned!

        :rtype: mpynode.MPyNode
        """

        plug = self.plug('targetParentMatrix')

        if plug.isDestination:

            return self.constraint.scene(plug.source().node())

        else:

            return None

    def targetRotateOrder(self):
        """
        Retrieves the rotate order for this constraint target.

        :rtype: int
        """

        if self.constraint.hasAttr('targetRotateOrder'):

            return self.plug('targetRotateOrder').asInt()

        else:

            return 0

    def targetOffsetTranslate(self):
        """
        Returns the offset translation for this constraint target.

        :rtype: om.MVector
        """
        
        # Check if attribute exists
        #
        if self.constraint.hasAttr('targetOffsetTranslate'):
        
            translatePlug = self.plug('targetOffsetTranslate')
            translateXPlug, translateYPlug, translateZPlug = translatePlug.child(0), translatePlug.child(1), translatePlug.child(2)
    
            return om.MVector(
                translateXPlug.asMDistance().asCentimeters(),
                translateYPlug.asMDistance().asCentimeters(),
                translateZPlug.asMDistance().asCentimeters()
            )
        
        else:
            
            return om.MVector.kZeroVector
        
    def setTargetOffsetTranslate(self, translation):
        """
        Updates the offset translation for this constraint target.

        :type translation: om.MVector
        :rtype: None
        """
        
        # Check if attribute exists
        #
        if not self.constraint.hasAttr('targetOffsetTranslate'):
            
            return
        
        # Update plug values
        #
        translatePlug = self.plug('targetOffsetTranslate')
        translateXPlug, translateYPlug, translateZPlug = translatePlug.child(0), translatePlug.child(1), translatePlug.child(2)

        translateXPlug.setMDistance(om.MDistance(translation.x, unit=om.MDistance.kCentimeters))
        translateYPlug.setMDistance(om.MDistance(translation.y, unit=om.MDistance.kCentimeters))
        translateZPlug.setMDistance(om.MDistance(translation.z, unit=om.MDistance.kCentimeters))

    def targetOffsetRotate(self):
        """
        Returns the offset rotation for this constraint target.

        :rtype: om.MEulerRotation
        """
        
        # Check if attribute exists
        #
        if self.constraint.hasAttr('targetOffsetRotate'):
            
            rotatePlug = self.plug('targetOffsetRotate')
            rotateXPlug, rotateYPlug, rotateZPlug = rotatePlug.child(0), rotatePlug.child(1), rotatePlug.child(2)
    
            return om.MEulerRotation(
                rotateXPlug.asMAngle().asRadians(),
                rotateYPlug.asMAngle().asRadians(),
                rotateZPlug.asMAngle().asRadians(),
                order=self.targetRotateOrder()
            )
        
        else:
            
            return om.MEulerRotation.kIdentity
        
    def setTargetOffsetRotate(self, rotation):
        """
        Updates the offset rotation for this constraint target.

        :type rotation: om.MEulerRotation
        :rtype: None
        """

        # Check if attribute exists
        #
        if not self.constraint.hasAttr('targetOffsetRotate'):
            
            return

        # Check if rotation requires reordering
        #
        rotateOrder = self.targetRotateOrder()

        if rotation.order != rotateOrder:

            rotation = rotation.reorder(rotateOrder)

        # Update plug values
        #
        rotatePlug = self.plug('targetOffsetRotate')
        rotateXPlug, rotateYPlug, rotateZPlug = rotatePlug.child(0), rotatePlug.child(1), rotatePlug.child(2)

        rotateXPlug.setMAngle(om.MAngle(rotation.x, unit=om.MAngle.kRadians))
        rotateYPlug.setMAngle(om.MAngle(rotation.y, unit=om.MAngle.kRadians))
        rotateZPlug.setMAngle(om.MAngle(rotation.z, unit=om.MAngle.kRadians))

    def targetOffsetScale(self):
        """
        Retrieves the offset rotation for this constraint target.
        This method is only supported by transform constraints!

        :rtype: om.MEulerRotation
        """

        # Check if attribute exists
        #
        if self.constraint.hasAttr('targetOffsetScale'):
                
            scalePlug = self.plug('targetOffsetScale')
            scaleXPlug, scaleYPlug, scaleZPlug = scalePlug.child(0), scalePlug.child(1), scalePlug.child(2)
    
            return om.MVector(
                scaleXPlug.asDouble(),
                scaleYPlug.asDouble(),
                scaleZPlug.asDouble()
            )
        
        else:
            
            return om.MVector.kOneVector
    
    def setTargetOffsetScale(self, scale):
        """
        Updates the offset rotation for this constraint target.

        :type scale: Union[om.MVector, Tuple[float, float, float]]
        :rtype: None
        """

        # Check if attribute exists
        #
        if not self.constraint.hasAttr('targetOffsetScale'):
            
            return

        # Update plug values
        #
        scalePlug = self.plug('targetOffsetScale')
        scaleXPlug, scaleYPlug, scaleZPlug = scalePlug.child(0), scalePlug.child(1), scalePlug.child(2)

        scaleXPlug.setDouble(scale[0])
        scaleYPlug.setDouble(scale[1])
        scaleZPlug.setDouble(scale[2])

    def resetTargetOffsets(self):
        """
        Resets the offsets on this constraint target.

        :rtype: None
        """

        self.setTargetOffsetTranslate(om.MVector.kZeroVector)
        self.setTargetOffsetRotate(om.MEulerRotation.kIdentity)
        self.setTargetOffsetScale(om.MVector.kOneVector)
    # endregion
