from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils

from . import transformmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ConstraintMixin(transformmixin.TransformMixin):
    """
    Overload of TransformMixin class used to interface with constraint nodes.
    """

    __apitype__ = (om.MFn.kConstraint, om.MFn.kPluginConstraintNode)

    __targets__ = {
        'translateX': 'targetTranslateX',
        'translateY': 'targetTranslateY',
        'translateZ': 'targetTranslateZ',
        'rotatePivotX': 'targetRotatePivotX',
        'rotatePivotY': 'targetRotatePivotY',
        'rotatePivotZ': 'targetRotatePivotZ',
        'rotatePivotTranslateX': 'targetRotateTranslateX',
        'rotatePivotTranslateY': 'targetRotateTranslateY',
        'rotatePivotTranslateZ': 'targetRotateTranslateZ',
        'scalePivotX': 'targetScalePivotX',
        'scalePivotY': 'targetScalePivotY',
        'scalePivotZ': 'targetScalePivotZ',
        'scalePivotTranslateX': 'targetScaleTranslateX',
        'scalePivotTranslateY': 'targetScaleTranslateY',
        'scalePivotTranslateZ': 'targetScaleTranslateZ',
        'rotateX': 'targetRotateX',
        'rotateY': 'targetRotateY',
        'rotateZ': 'targetRotateZ',
        'rotateOrder': 'targetRotateOrder',
        'jointOrientX': 'targetJointOrientX',
        'jointOrientY': 'targetJointOrientY',
        'jointOrientZ': 'targetJointOrientZ',
        'scaleX': 'targetScaleX',
        'scaleY': 'targetScaleY',
        'scaleZ': 'targetScaleZ',
        'inverseScale': 'targetInverseScale',
        'segmentScaleCompensate': 'targetScaleCompensate'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ',
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ',
        'constraintScaleX': 'scaleX',
        'constraintScaleY': 'scaleY',
        'constraintScaleZ': 'scaleZ'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(ConstraintMixin, self).__init__(*args, **kwargs)

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

        :type constraintObject: mpy.mpynode.MPyNode
        :keyword maintainOffset: bool
        :keyword skipTranslateX: bool
        :keyword skipTranslateY: bool
        :keyword skipTranslateZ: bool
        :keyword skipRotateX: bool
        :keyword skipRotateY: bool
        :keyword skipRotateZ: bool
        :keyword skipScaleX: bool
        :keyword skipScaleY: bool
        :keyword skipScaleZ: bool
        :rtype: None
        """

        # Check for redundancy
        #
        if constraintObject == self.constraintObject():

            return

        # Re-parent this constraint
        #
        self.setParent(constraintObject)

        # Update constraint name
        #
        constraintName = '{nodeName}_{typeName}1'.format(nodeName=constraintObject.displayName(), typeName=self.typeName)
        self.setName(constraintName)

        # Update rest matrix
        #
        restMatrix = constraintObject.getAttr('matrix')
        self.setRestMatrix(restMatrix)

        # Connect output attributes
        #
        for (sourceName, destinationName) in self.__outputs__.items():

            # Check if attribute should be skipped
            #
            attributeName = destinationName[0].upper() + destinationName[1:]
            key = 'skip{attributeName}'.format(attributeName=attributeName)

            skipAttribute = kwargs.get(key, False)

            if skipAttribute:

                log.info('Skipping constraint attribute: %s' % destinationName)
                continue

            # Check if attributes exist
            #
            if not self.hasAttr(sourceName) or not constraintObject.hasAttr(destinationName):

                log.info('Unable to locate constraint attributes: %s and %s' % (sourceName, destinationName))
                continue

            # Get associated plugs
            #
            source = self.findPlug(sourceName)
            destination = constraintObject.findPlug(destinationName)

            # Connect plugs
            #
            self.breakConnections(source, source=False, destination=True)
            self.connectPlugs(source, destination, force=True)

        # Update constraint parent inverse matrix
        #
        source = constraintObject.findPlug('parentInverseMatrix[%s]' % constraintObject.instanceNumber())
        destination = self.findPlug('constraintParentInverseMatrix')

        constraintObject.connectPlugs(source, destination, force=True)

        # Check if constraint supports rotation order
        # This is only seen in orient and transform constraints
        #
        if self.hasAttr('constraintRotateOrder'):

            constraintObject.connectPlugs('rotateOrder', self.findPlug('constraintRotateOrder'), force=True)

        # Check if constraint supports joint orient
        # This is only seen in orient and transform constraints
        #
        if self.hasAttr('constraintJointOrient') and constraintObject.hasAttr('jointOrient'):

            # Connect child plugs
            #
            source = constraintObject.findPlug('jointOrient')
            destination = self.findPlug('constraintJointOrient')

            for i in range(source.numChildren()):

                constraintObject.connectPlugs(source.child(i), destination.child(i), force=True)

    def interpolationType(self):
        """
        Getter method used to retrieve the interpolation type for this constraint.

        :rtype: int
        """

        return om.MPlug(self.object(), self.attribute('interpType')).asInt()

    def setInterpolationType(self, interpolationType):
        """
        Setter method used to update the interpolation type for this constraint.

        :type interpolationType: int
        :rtype: None
        """

        om.MPlug(self.object(), self.attribute('interpType')).setInt(interpolationType)

    def offset(self):
        """
        Getter method used to retrieve the offset for this constraint.
        Only a few constraints support this method such as point and orient constraints!

        :rtype: om.MVector
        """

        return om.MVector(
            om.MPlug(self.object(), self.attribute('offsetX')).asFloat(),
            om.MPlug(self.object(), self.attribute('offsetY')).asFloat(),
            om.MPlug(self.object(), self.attribute('offsetZ')).asFloat()
        )

    def setOffset(self, offset):
        """
        Setter method used to update the offset for this constraint.
        Only a few constraints support this method such as point and orient constraints!

        :type offset: om.MVector
        :rtype: None
        """

        om.MPlug(self.object(), self.attribute('offsetX')).setFloat(offset.x)
        om.MPlug(self.object(), self.attribute('offsetY')).setFloat(offset.y)
        om.MPlug(self.object(), self.attribute('offsetZ')).setFloat(offset.z),

    def targets(self):
        """
        Collects all of the available constraint targets.

        :rtype: list[ConstraintTarget]
        """

        return list(self.iterTargets())

    def targetObjects(self):
        """
        Retrieves the target objects driving this constraint.

        :rtype: list[mpynode.MPyNode]
        """

        return [x.targetObject() for x in self.iterTargets()]

    def iterTargets(self):
        """
        Generator method used to iterate through all available constraint targets.

        :rtype: iter
        """

        # Iterate through target indices
        #
        for i in range(self.targetCount()):

            yield ConstraintTarget(self, index=i)

    def targetCount(self):
        """
        Evaluates the number of active target elements available.

        :rtype: int
        """

        return om.MPlug(self.object(), self.attribute('target')).evaluateNumElements()

    def addTarget(self, target, maintainOffset=True):
        """
        Adds a new target to this constraint.

        :type target: mpynode.MPyNode
        :type maintainOffset: bool
        :rtype: int
        """

        # Iterate through required target attributes
        #
        plug = self.findPlug('target')
        index = plug.evaluateNumElements()

        for (sourceName, destinationName) in self.__targets__.items():

            # Check if constraint has attribute
            #
            if not target.hasAttr(sourceName) or not self.hasAttr(destinationName):

                log.info('Unable to locate constraint attributes: %s and %s' % (sourceName, destinationName))
                continue

            # Connect plugs
            #
            source = target.findPlug(sourceName)
            destination = self.findPlug('target[%s].%s' % (index, destinationName))

            self.connectPlugs(source, destination)

        # Connect parent matrix attribute
        #
        source = target.findPlug('parentMatrix[%s]' % target.instanceNumber())
        destination = self.findPlug('target[%s].targetParentMatrix' % index)

        self.connectPlugs(source, destination)

        # Connect weight attributes
        #
        nodeName = target.displayName()

        attribute = self.addAttr(
            longName='{nodeName}W{index}'.format(nodeName=nodeName, index=index),
            attributeType='float',
            min=0.0, max=1.0
        )

        source = om.MPlug(self.object(), attribute)
        destination = self.findPlug('target[%s].targetWeight' % index)

        self.connectPlugs(source, destination)

        # Enable weight attribute
        #
        source.setFloat(1.0)

        # Return new target index
        #
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

    def removeTarget(self, index):

        pass

    def restTranslate(self, context=om.MDGContext.kNormal):
        """
        Returns the rest translate component from this constraint.
        This value is used when there are no target weights.

        :type context: om.MDGContext
        :rtype: om.MVector
        """

        return om.MVector(
            self.findPlug('restTranslateX').asFloat(context=context),
            self.findPlug('restTranslateY').asFloat(context=context),
            self.findPlug('restTranslateZ').asFloat(context=context)
        )

    def setRestTranslate(self, restTranslate):
        """
        Updates the rest translate for this constraint.

        :type restTranslate: om.MVector
        :rtype: None
        """

        # Assign translation to plug
        #
        self.findPlug('restTranslateX').setFloat(restTranslate.x)
        self.findPlug('restTranslateY').setFloat(restTranslate.y)
        self.findPlug('restTranslateZ').setFloat(restTranslate.z)

    def restRotate(self, context=om.MDGContext.kNormal):
        """
        Returns the rest rotation component from this constraint.
        This value is used when there are no target weights.

        :type context: om.MDGContext
        :rtype: om.MEulerRotation
        """

        return om.MEulerRotation(
            self.findPlug('restRotateX').asFloat(context=context),
            self.findPlug('restRotateY').asFloat(context=context),
            self.findPlug('restRotateZ').asFloat(context=context),
            order=self.rotateOrder(context=context)
        )

    def setRestRotate(self, restRotation):
        """
        Updates the rest rotate for this constraint.

        :type restRotation: om.MEulerRotation
        :rtype: None
        """

        # Check if rotation needs reordering
        #
        rotateOrder = self.rotateOrder()

        if restRotation.order != rotateOrder:

            restRotation = restRotation.reorder(rotateOrder)

        # Assign rotation to plugs
        #
        self.findPlug('restRotateX').setFloat(restRotation.x)
        self.findPlug('restRotateY').setFloat(restRotation.y)
        self.findPlug('restRotateZ').setFloat(restRotation.z)

    def restScale(self, context=om.MDGContext.kNormal):
        """
        Returns the rest translate component from this constraint.
        This value is used when there are no target weights.

        :type context: om.MDGContext
        :rtype: list[float, float, float]
        """

        return [
            self.findPlug('restScaleX').asFloat(context=context),
            self.findPlug('restScaleY').asFloat(context=context),
            self.findPlug('restScaleZ').asFloat(context=context)
        ]

    def setRestScale(self, restScale):
        """
        Updates the rest translate for this constraint.

        :type restScale: list[float, float, float]
        :rtype: None
        """

        # Assign scale to plugs
        #
        self.findPlug('restScaleX').setFloat(restScale[0])
        self.findPlug('restScaleY').setFloat(restScale[1])
        self.findPlug('restScaleZ').setFloat(restScale[2])

    def restMatrix(self):
        """
        Computes a transform matrix based off the rest components.

        :rtype: om.MMatrix
        """

        # Compose rest matrix
        #
        translateMatrix = transformutils.createTranslateMatrix(self.restTranslate())
        rotateMatrix = transformutils.createRotationMatrix(self.restRotate())
        scaleMatrix = transformutils.createScaleMatrix(1.0)

        return scaleMatrix * rotateMatrix * translateMatrix

    def setRestMatrix(self, restMatrix):
        """
        Updates the rest matrix for this constraint by changing the rest components.

        :type restMatrix: om.MMatrix
        :rtype: None
        """

        # Decompose rest matrix
        #
        translate, rotate, scale = transformutils.decomposeTransformMatrix(restMatrix, rotateOrder=self.rotateOrder())

        # Check if constraint has rest translate
        #
        if self.hasAttr('restTranslate'):

            self.setRestTranslate(translate)

        # Check if constraint has rest rotate
        #
        if self.hasAttr('restRotate'):

            self.setRestRotate(rotate)

        # Check if constraint has rest scale
        #
        if self.hasAttr('restScale'):

            self.setRestScale(scale)

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


class ConstraintTarget(object):
    """
    Base class used to interface with constraint targets.
    """

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

    def resetOffsetTransform(self):
        pass
