import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.generators.inclusiverange import inclusiveRange
from dcc.maya.libs import plugutils, transformutils, shapeutils, animutils
from dcc.maya.json import mshapeparser
from dcc.maya.decorators.animate import animate
from . import dagmixin
from .. import mpyattribute, mpycontext

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransformMixin(dagmixin.DagMixin):
    """
    Overload of `DagMixin` that interfaces with transform nodes.
    """

    # region Attributes
    inheritsTransform = mpyattribute.MPyAttribute('inheritsTransform')
    displayHandle = mpyattribute.MPyAttribute('displayHandle')
    displayScalePivot = mpyattribute.MPyAttribute('displayScalePivot')
    displayRotatePivot = mpyattribute.MPyAttribute('displayRotatePivot')
    displayLocalAxis = mpyattribute.MPyAttribute('displayLocalAxis')
    minTransLimitEnable = mpyattribute.MPyAttribute('minTransLimitEnable')
    maxTransLimitEnable = mpyattribute.MPyAttribute('maxTransLimitEnable')
    minRotLimitEnable = mpyattribute.MPyAttribute('minRotLimitEnable')
    maxRotLimitEnable = mpyattribute.MPyAttribute('maxRotLimitEnable')
    minScaleLimitEnable = mpyattribute.MPyAttribute('minScaleLimitEnable')
    maxScaleLimitEnable = mpyattribute.MPyAttribute('maxScaleLimitEnable')
    # endregion

    # region Dunderscores
    __api_type__ = (om.MFn.kTransform, om.MFn.kPluginTransformNode)
    # endregion

    # region Methods
    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnTransform
        """

        return super(TransformMixin, self).functionSet()

    def setParent(self, parent, absolute=False):
        """
        Updates the parent for this node.

        :type parent: Union[None, str, om.MObject, DagMixin]
        :type absolute: bool
        :rtype: None
        """

        # Cache world-matrix
        #
        worldMatrix = self.worldMatrix()

        # Call parent method
        #
        super(TransformMixin, self).setParent(parent)

        # Check if world-matrix should be preserved
        #
        if absolute:

            matrix = worldMatrix * self.exclusiveMatrixInverse()
            self.setMatrix(matrix, skipScale=True)

    def translation(self, space=om.MSpace.kTransform, time=None):
        """
        Returns the transform's translation component.

        :type space: int
        :type time: Union[int, None]
        :rtype: om.MVector
        """

        with mpycontext.MPyContext(time=time):

            return transformutils.getTranslation(self.dagPath(), space=space)

    def setTranslation(self, translation, space=om.MSpace.kTransform):
        """
        Updates the transform's translation component.

        :type translation: om.MVector
        :type space: int
        :rtype: None
        """

        transformutils.setTranslation(self.dagPath(), translation, space=space)

    def resetTranslation(self):
        """
        Resets the transform's translation component back to zero.

        :rtype: None
        """

        transformutils.resetTranslation(self.dagPath())

    def translateTo(self, position):
        """
        Translates this node to the specified position.
        Unlike `setTranslation`, this method adds the translational difference to the current transform matrix.

        :type position: om.MVector
        :rtype: None
        """

        transformutils.translateTo(self.dagPath(), position)

    def rotateOrder(self):
        """
        Returns the transform's rotation order.

        :rtype: int
        """

        return transformutils.getRotationOrder(self.dagPath())

    def setRotateOrder(self, rotateOrder):
        """
        Updates the transform's rotation order.

        :type rotateOrder: int
        :rtype: None
        """

        self.setAttr('rotateOrder', rotateOrder)

    def eulerRotation(self, time=None):
        """
        Returns the transform's rotation component.

        :type time: Union[int, None]
        :rtype: om.MEulerRotation
        """

        with mpycontext.MPyContext(time=time):

            return transformutils.getEulerRotation(self.dagPath())

    def setEulerRotation(self, eulerRotation):
        """
        Updates the transform's euler rotation component.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        transformutils.setEulerRotation(self.dagPath(), eulerRotation)

    def resetEulerRotation(self):
        """
        Resets the transform's rotation component back to zero.

        :rtype: None
        """

        transformutils.resetEulerRotation(self.dagPath())

    def rotateTo(self, eulerRotation):
        """
        Rotates this node to the specified orientation.
        Unlike `setEulerRotation`, this method adds the rotational difference to the current transform matrix.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        transformutils.rotateTo(self.dagPath(), eulerRotation)

    def preEulerRotation(self):
        """
        Returns the transform's pre-euler rotation component.

        :rtype: om.MEulerRotation
        """

        return om.MEulerRotation()

    def setPreEulerRotation(self, eulerRotation):
        """
        Updates the transform's pre-euler rotation component.

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        pass

    def resetPreEulerRotation(self):
        """
        Resets the transform's pre-euler rotation component back to zero.

        :rtype: None
        """

        self.setPreEulerRotation(om.MEulerRotation())

    def scale(self, time=None):
        """
        Returns the transform's scale component.

        :type time: Union[int, None]
        :rtype: List[float, float, float]
        """

        with mpycontext.MPyContext(time=time):

            return transformutils.getScale(self.dagPath())

    def setScale(self, scale):
        """
        Updates the transform's scale component

        :type scale: List[float, float, float]
        :rtype: None
        """

        # Check if scale change is required
        # Introducing non-unit scale values can cause Maya to not behave as expected!
        #
        if not transformutils.isClose(self.scale(), scale):

            transformutils.setScale(self.dagPath(), scale)

    def resetScale(self):
        """
        Resets the transform's scale component back to one.

        :rtype: None
        """

        transformutils.resetScale(self.dagPath())

    def scaleTo(self, scale):
        """
        Scales this node to the specified size.
        Unlike `setScale`, this method adds the scalar difference to the current transform matrix.

        :type scale: Union[List[float, float, float], om.MVector]
        :rtype: None
        """

        transformutils.scaleTo(self.dagPath(), scale)

    def freezePivots(self, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Pushes the transform's translation into its pivots.

        :type includeTranslate: bool
        :type includeRotate: bool
        :type includeScale: bool
        :rtype: None
        """

        transformutils.freezePivots(
            self.dagPath(),
            includeTranslate=includeTranslate,
            includeRotate=includeRotate,
            includeScale=includeScale
        )

    def unfreezePivots(self):
        """
        Pushes the transform's pivots back into translation.

        :rtype: None
        """

        transformutils.unfreezePivots(self.dagPath())

    def resetPivots(self):
        """
        Resets the transform's pivots.

        :rtype: None
        """

        transformutils.resetPivots(self.dagPath())

    def setMatrix(self, matrix, **kwargs):
        """
        Updates the local transformation matrix for this transform.

        :type matrix: om.MMatrix
        :key skipTranslate: bool
        :key skipRotate: bool
        :key skipScale: bool
        :rtype: None
        """

        transformutils.applyTransformMatrix(self.dagPath(), matrix, **kwargs)

    def resetMatrix(self):
        """
        Resets all the transform components back to zero.

        :rtype: None
        """

        self.resetTranslation()
        self.resetPreEulerRotation()
        self.resetEulerRotation()
        self.resetScale()

    def setWorldMatrix(self, worldMatrix, **kwargs):
        """
        Updates the world transformation matrix for this transform.

        :type worldMatrix: om.MMatrix
        :key skipTranslate: bool
        :key skipRotate: bool
        :key skipScale: bool
        :rtype: None
        """

        parentInverseMatrix = self.parentInverseMatrix()
        matrix = worldMatrix * parentInverseMatrix

        self.setMatrix(matrix, **kwargs)

    def distanceBetween(self, otherNode):
        """
        Returns the distance between this and the other node.

        :type otherNode: TransformMixin
        :rtype: float
        """

        position = self.translation(space=om.MSpace.kWorld)
        otherPosition = otherNode.translation(space=om.MSpace.kWorld)

        return om.MPoint(position).distanceTo(om.MPoint(otherPosition))

    def keyTransform(self, ensure=False):
        """
        Keys just the transform component attributes.

        :type ensure: bool
        :rtype: None
        """

        # Iterate through transform attributes
        #
        for plug in self.iterPlugs(channelBox=True, affectsWorldSpace=True, skipUserAttributes=True):

            # Check if child is keyable
            #
            if plug.isKeyable and not plug.isLocked:

                self.keyAttr(plug)

            else:

                continue

    @animate
    def alignTransformTo(self, transform, **kwargs):
        """
        Aligns this transform to the other transform over a period of time.

        :type transform: TransformMixin
        :key maintainOffset: bool
        :key startTime: int
        :key endTime: int
        :key step: int
        :rtype: None
        """

        # Get animation range
        #
        startTime = kwargs.pop('startTime', self.scene.time)
        endTime = kwargs.pop('endTime', self.scene.time)
        step = kwargs.pop('step', 1)

        # Get offset matrices
        #
        maintainOffset = kwargs.pop('maintainOffset', False)
        maintainTranslate = kwargs.pop('maintainTranslate', maintainOffset)
        maintainRotate = kwargs.pop('maintainRotate', maintainOffset)
        maintainScale = kwargs.pop('maintainScale', maintainOffset)

        offsetMatrix = self.worldMatrix(time=startTime) * transform.worldInverseMatrix(time=startTime)
        translateOffsetMatrix = transformutils.createTranslateMatrix(offsetMatrix) if maintainTranslate else om.MMatrix.kIdentity
        rotateOffsetMatrix = transformutils.createRotationMatrix(offsetMatrix) if maintainRotate else om.MMatrix.kIdentity
        scaleOffsetMatrix = transformutils.createScaleMatrix(offsetMatrix) if maintainScale else om.MMatrix.kIdentity

        # Iterate through time range
        #
        self.clearKeys(animationRange=(startTime, endTime), skipUserAttributes=True, **kwargs)

        for time in inclusiveRange(startTime, endTime, step):

            # Go to time
            #
            self.scene.time = time

            # Calculate target matrix and update transform
            #
            worldMatrix = transform.worldMatrix()
            parentInverseMatrix = self.parentInverseMatrix()
            localMatrix = ((scaleOffsetMatrix * rotateOffsetMatrix * translateOffsetMatrix) * worldMatrix) * parentInverseMatrix

            self.setMatrix(localMatrix, **kwargs)

    def cacheTransformations(self, animationRange=None, step=1, worldSpace=False):
        """
        Returns a dictionary of time-matrix items.
        If no range is specified then the matrices at each keyframe are returned instead!

        :type animationRange: Union[Tuple[int, int], None]
        :type step: Union[int, None]
        :type worldSpace: bool
        :rtype: Dict[int, om.MMatrix]
        """

        # Check if an animation range was supplied
        #
        if not stringutils.isNullOrEmpty(animationRange):

            # Get matrices at times
            #
            startTime, endTime = animationRange
            matrices = {}

            for time in inclusiveRange(startTime, endTime, step):

                matrices[time] = self.worldMatrix(time=time) if worldSpace else self.matrix(time=time)

            return matrices

        else:

            # Collect time inputs
            #
            times = set()

            for plug in self.iterPlugs(channelBox=True):

                # Check if plug is animated
                #
                if not plugutils.isAnimated(plug):

                    continue

                # Add curve inputs
                #
                animCurve = self.scene(plug.source().node())
                times.update(set(animCurve.inputs()))

            # Get matrices at times
            #
            matrices = {}

            for time in sorted(times):

                matrices[time] = self.worldMatrix(time=time) if worldSpace else self.matrix(time=time)

            return matrices

    def syncTransformKeys(self):
        """
        Synchronizes the time inputs for all transform keys.

        :rtype: Dict[str, List[keyframe.Keyframe]]
        """

        translateCache = animutils.synchronizeCompoundInputs(self.findPlug('translate'))
        rotateCache = animutils.synchronizeCompoundInputs(self.findPlug('rotate'))
        scaleCache = animutils.synchronizeCompoundInputs(self.findPlug('scale'))

        cache = {}
        cache.update(translateCache)
        cache.update(rotateCache)
        cache.update(scaleCache)

        return cache

    def copyTransform(self, other, **kwargs):
        """
        Copies the transform of the supplied node.

        :type other: TransformMixin
        :rtype: None
        """

        matrix = other.worldMatrix() * self.parentInverseMatrix()
        self.setMatrix(matrix, **kwargs)

    def resetTransform(self, skipUserAttributes=False):
        """
        Resets all the channel-box plugs back to their default value.

        :rtype: None
        """

        for plug in self.iterPlugs(channelBox=True, skipUserAttributes=skipUserAttributes):

            self.resetAttr(plug)

    def freezeTransform(self, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Pushes the transform's matrix into the parent offset matrix.

        :type includeTranslate: bool
        :type includeRotate: bool
        :type includeScale: bool
        :rtype: None
        """

        transformutils.freezeTransform(
            self.dagPath(),
            includeTranslate=includeTranslate,
            includeRotate=includeRotate,
            includeScale=includeScale
        )

    def unfreezeTransform(self):
        """
        Pushes the transform's parent offset matrix back into its matrix.

        :rtype: None
        """

        transformutils.unfreezeTransform(self.dagPath())

    def detectMirroring(self):
        """
        Detects the mirror settings for this transform.
        Each transform component uses the keyword pattern: mirrorTranslateX, etc

        :rtype: bool
        """

        # Compare parent matrices
        #
        matrix = self.parentMatrix()
        xAxis, yAxis, zAxis, pos = transformutils.breakMatrix(matrix, normalize=True)
        mirrorXAxis, mirrorYAxis, mirrorZAxis = list(map(transformutils.mirrorVector, (xAxis, yAxis, zAxis)))

        otherTransform = self.getOppositeNode()
        otherMatrix = otherTransform.parentMatrix()
        otherXAxis, otherYAxis, otherZAxis, otherPos = transformutils.breakMatrix(otherMatrix, normalize=True)

        mirrorTranslateX = (mirrorXAxis * otherXAxis) < 0.0
        mirrorTranslateY = (mirrorYAxis * otherYAxis) < 0.0
        mirrorTranslateZ = (mirrorZAxis * otherZAxis) < 0.0

        # Compose mirror settings and update user properties
        #
        settings = {
            'mirrorTranslateX': mirrorTranslateX,
            'mirrorTranslateY': mirrorTranslateY,
            'mirrorTranslateZ': mirrorTranslateZ,
            'mirrorRotateX': not mirrorTranslateX,
            'mirrorRotateY': not mirrorTranslateY,
            'mirrorRotateZ': not mirrorTranslateZ,
        }

        log.info('Detecting "%s" > "%s" mirror settings: %s' % (self.name(), otherTransform.name(), settings))
        self.userProperties.update(settings)

        return True

    def mirrorTransform(self, pull=False, skipUserAttributes=False, includeKeys=False, animationRange=None, insertAt=None):
        """
        Mirrors this transform to the opposite node.

        :type pull: bool
        :type skipUserAttributes: bool
        :type includeKeys: bool
        :type animationRange: Union[Tuple[int, int], None]
        :type insertAt: Union[int, None]
        :rtype: None
        """

        # Iterate through channel-box plugs
        #
        for plug in self.iterPlugs(channelBox=True, skipUserAttributes=skipUserAttributes):

            self.mirrorAttr(
                plug,
                pull=pull,
                includeKeys=includeKeys,
                animationRange=animationRange,
                insertAt=insertAt
            )

    def isController(self):
        """
        Checks if this transform node has been tagged as a controller.

        :rtype: bool
        """

        return self.controllerTag() is not None

    def controllerTag(self, create=False):
        """
        Returns the controller tag for this transform node.
        This method will raise a type error if multiple tags are found!

        :type create: bool
        :rtype: mpy.builtins.controllermixin.ControllerMixin
        """

        # Find associated controller tag
        #
        plug = self.findPlug('message')
        destinations = plug.destinations()

        tag = None

        for destination in destinations:

            # Check if this is a controller node
            #
            node = destination.node()
            plugName = destination.partialName(useLongNames=True)

            if node.hasFn(om.MFn.kControllerTag) and plugName == 'controllerObject':

                tag = self.scene(node)
                break

            else:

                continue

        # Evaluate results
        #
        if tag is not None:

            return tag

        elif create:

            return self.tagAsController()

        else:

            return None

    def tagAsController(self, **kwargs):
        """
        Tags this transform node as a controller.
        If this transform is already tagged then that controller will be returned.

        :rtype: mpy.builtins.controllermixin.ControllerMixin
        """

        # Check if tag already exists
        #
        controllerTag = self.controllerTag()

        if controllerTag is None:

            controllerTag = self.scene.createNode('controller', name='{nodeName}_tag'.format(nodeName=self.name()))
            controllerTag.controllerObject = self.object()

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', None)

        if parent is not None:

            parentTag = parent.controllerTag(create=True)
            parentTag.connectPlugs('message', controllerTag['parent'], force=True)
            parentTag.connectPlugs('prepopulate', controllerTag['prepopulate'], force=True)

        # Check if children were supplied
        #
        children = kwargs.get('children', [])

        for (i, child) in enumerate(children):

            childTag = child.controllerTag(create=True)
            controllerTag.connectPlugs(childTag['parent'], f'children[{i}]', force=True)

        return controllerTag

    def addGlobalScale(self):
        """
        Adds a global scale attribute to this transform.
        Once done all the scale attributes will be hidden.

        :rtype: None
        """

        # Check if attribute already exists
        #
        if self.hasAttr('globalScale'):

            return

        # Create global scale attribute
        #
        self.addAttr(longName='globalScale', shortName='gs', attributeType='float', min=0.0, default=1.0, channelBox=True)
        self.connectPlugs('globalScale', 'scaleX')
        self.connectPlugs('globalScale', 'scaleY')
        self.connectPlugs('globalScale', 'scaleZ')
        self.hideAttr('scaleX', 'scaleY', 'scaleZ', lock=True)

    def prepareChannelBoxForAnimation(self):
        """
        Prepares the channel box for animation.
        Right now this means hiding the visibility attribute and restoring the rotate-order for animators.

        :rtype: None
        """

        self.hideAttr('visibility')
        self.showAttr('rotateOrder')

    def iterConstraints(self, typeName='constraint'):
        """
        Returns a generator that yields constraints from this transform.

        :type typeName: str
        :rtype: Iterator[mpy.builtins.constraintmixin.ConstraintMixin]
        """

        # Iterate through connections
        #
        plugs = self.getConnections()
        typeNames = mc.nodeType(typeName, isTypeName=True, derived=True)

        constraints = {}

        for plug in plugs:

            # Check if plug is destination
            #
            if not plug.isDestination:

                continue

            # Evaluate source node
            #
            source = self.scene(plug.source().node())

            if not (source.typeName in typeNames):

                continue

            # Check if constraint was already yielded
            #
            hashCode = source.hashCode()
            yielded = constraints.get(hashCode, False)

            if not yielded:

                constraints[hashCode] = True
                yield source

    def constraints(self, typeName='constraint'):
        """
        Retrieves a list of constraints that are driving this transform.

        :type typeName: str
        :rtype: List[mpy.builtins.constraintmixin.ConstraintMixin]
        """

        return list(self.iterConstraints(typeName=typeName))

    def constraintCount(self):
        """
        Counts the number of constraints connected to this transform.

        :rtype: int
        """

        return len(self.constraints())

    def isConstrained(self):
        """
        Evaluates if this transform has any constraints.

        :rtype: bool
        """

        return self.constraintCount() > 0

    def addConstraint(self, typeName, targets, **kwargs):
        """
        Adds a constraint node to this transform.
        Any constrained attributes can be skipped by supplying them as keyword arguments: skipTranslateX, etc

        :type typeName: str
        :type targets: List[TransformMixin]
        :key maintainOffset: bool
        :rtype: mpy.builtins.constraintmixin.ConstraintMixin
        """

        # Check if constraint already exists
        #
        constraint = self.findConstraint(typeName)

        if constraint is not None:

            return constraint

        # Create constraint and add targets
        #
        constraint = self.scene.createNode(typeName)
        constraint.setConstraintObject(self, **kwargs)
        constraint.addTargets(targets, **kwargs)

        return constraint

    def findConstraint(self, typeName):
        """
        Returns the constraint with the specified type name.
        If no constraint exists then none is returned!

        :type typeName: str
        :rtype: mpy.builtins.constraintmixin.ConstraintMixin
        """

        found = self.constraints(typeName=typeName)
        numFound = len(found)

        if numFound == 0:

            return None

        elif numFound == 1:

            return found[0]

        else:

            raise TypeError(f'findConstraint() expects to find 1 unique constraint ({numFound} found)!')

    def hasConstraint(self, typeName):
        """
        Evaluates if this transform has the specified constraint.

        :type typeName: str
        :rtype: bool
        """

        return self.findConstraint(typeName) is not None

    def removeConstraints(self):
        """
        Removes all constraints from this transform.

        :rtype: None
        """

        constraints = self.constraints()

        for constraint in constraints:

            constraint.delete()

    def addSpaceSwitch(self, spaces, **kwargs):
        """
        Adds a space switcher to this transform.

        :type spaces: List[transformmixin.TransformMixin]
        :key name: str
        :key maintainOffset: bool
        :key skipTranslate: bool
        :key skipRotate: bool
        :key skipScale: bool
        :rtype: spaceswitchmixin.SpaceSwitchMixin
        """

        # Create space switcher
        #
        name = kwargs.get('name', f'{self.name()}_spaceSwitch1')

        spaceSwitch = self.scene.createNode('spaceSwitch', name=name)
        spaceSwitch.setDriven(self, **kwargs)
        spaceSwitch.addSpaces(spaces, **kwargs)

        return spaceSwitch

    def addShape(self, shape, **kwargs):
        """
        Adds the specified shape to this transform node.
        See the shapes directory for a list of accepted shape names!

        :type shape: str
        :key localPosition: Union[Tuple[float, float, float], om.MVector]
        :key localRotate: Union[Tuple[float, float, float], om.MVector]
        :key localScale: Union[Tuple[float, float, float], om.MVector]
        :key lineWidth: float
        :rtype: List[mpy.builtins.shapemixin.ShapeMixin]
        """

        filePath = self.scene.getAbsoluteShapePath(shape)
        shapes = mshapeparser.loadShapeTemplate(filePath, parent=self.object(), **kwargs)

        return list(map(self.scene.__call__, shapes))

    def addStar(self, size, **kwargs):
        """
        Adds a star shape to this transform.

        :key numPoints: int
        :rtype: mpy.plugins.pointhelpermixin.PointHelperMixin
        """

        curveData = shapeutils.createStar(1.0, 0.5, **kwargs)
        controlPoints = om.MFnNurbsCurve(curveData).cvPositions()

        pointHelper = self.addPointHelper('custom')
        pointHelper.size = size
        pointHelper.setAttr('controlPoints', controlPoints)

        shapeutils.colorizeShape(pointHelper.object(), **kwargs)

        return pointHelper

    def addLocator(self, *args, **kwargs):
        """
        Adds a locator shape to this transform.

        :key localPosition: Tuple[float, float, float]
        :key localScale: Tuple[float, float, float]
        :rtype: mpy.builtins.locatormixin.LocatorMixin
        """

        # Create locator shape
        #
        name = '{name}Shape'.format(name=self.name())
        locator = self.scene.createNode('locator', name=name, parent=self)

        # Check if local position was supplied
        #
        localPosition = kwargs.get('localPosition', None)

        if localPosition is not None:

            locator.setAttr('localPositionX', localPosition[0])
            locator.setAttr('localPositionY', localPosition[1])
            locator.setAttr('localPositionZ', localPosition[2])

        # Check if local scale was supplied
        #
        localScale = kwargs.get('localScale', None)

        if localScale is not None:

            locator.setAttr('localScaleX', localScale[0])
            locator.setAttr('localScaleY', localScale[1])
            locator.setAttr('localScaleZ', localScale[2])

        # Colourize locator
        #
        shapeutils.colorizeShape(locator.dagPath(), **kwargs)

        return locator

    def addPointHelper(self, *args, **kwargs):
        """
        Adds a point helper shape to this transform.

        :key size: float
        :key localPosition: Tuple[float, float, float]
        :key localRotate: Tuple[float, float, float]
        :key localScale: Tuple[float, float, float]
        :rtype: mpy.plugins.pointhelpermixin.PointHelperMixin
        """

        # Create point helper shape
        #
        name = '{name}Shape'.format(name=self.name())
        pointHelper = self.scene.createNode('pointHelper', name=name, parent=self)

        # Check if any shapes were supplied
        #
        numArgs = len(args)

        if numArgs > 0:

            # Disable all default shapes
            #
            for attribute in pointHelper.iterAttr(category='Drawable'):

                pointHelper[attribute].setBool(False)

            # Iterate through shape names
            #
            for shape in args:

                pointHelper[shape].setBool(True)

        else:

            log.debug('Using default point helper shapes...')

        # Set shape size
        #
        size = kwargs.get('size', None)

        if size is not None:

            pointHelper.setAttr('size', size)

        # Check if local position was supplied
        #
        localPosition = kwargs.get('localPosition', None)

        if localPosition is not None:

            pointHelper.setAttr('localPositionX', localPosition[0])
            pointHelper.setAttr('localPositionY', localPosition[1])
            pointHelper.setAttr('localPositionZ', localPosition[2])

        # Check if local rotation was supplied
        #
        localRotate = kwargs.get('localRotate', None)

        if localRotate is not None:

            pointHelper.setAttr('localRotateX', localRotate[0])
            pointHelper.setAttr('localRotateY', localRotate[1])
            pointHelper.setAttr('localRotateZ', localRotate[2])

        # Check if local scale was supplied
        #
        localScale = kwargs.get('localScale', None)

        if localScale is not None:

            pointHelper.setAttr('localScaleX', localScale[0])
            pointHelper.setAttr('localScaleY', localScale[1])
            pointHelper.setAttr('localScaleZ', localScale[2])

        # Colourize point helper
        #
        shapeutils.colorizeShape(pointHelper.dagPath(), **kwargs)

        return pointHelper

    def addCamera(self, **kwargs):
        """
        Adds a camera shape to this transform.

        :rtype: mpy.builtins.cameramixin.CameraMixin
        """

        # Create camera shape
        #
        name = '{name}Shape'.format(name=self.name())
        camera = self.scene.createNode('camera', name=name, parent=self)

        # Edit camera scale
        #
        scale = kwargs.get('scale', 1.0)
        camera.cameraScale = scale

        return camera

    def renameShapes(self):
        """
        Renames the shapes under this transform.

        :rtype: None
        """

        # Evaluate number of shapes
        #
        name = self.name()

        shapes = self.shapes()
        numShapes = len(shapes)

        if numShapes == 0:

            return

        elif numShapes == 1:

            shape = shapes[0]
            originalName = shape.name()
            newName = f'{name}Shape'

            log.info(f'Renaming {originalName} > {newName}')
            shape.setName(newName)

        else:

            for (i, shape) in enumerate(shapes, start=1):

                originalName = shape.name()
                newName = f'{name}Shape{i}'

                log.info(f'Renaming {originalName} > {newName}')
                shape.setName(newName)

    def removeShapes(self):
        """
        Removes all shapes underneath this transform.
        This method is NOT undoable!

        :rtype: None
        """

        # Iterate through shapes
        #
        shapes = self.shapes()

        for shape in shapes:

            shape.delete()

    def colorizeShapes(self, **kwargs):
        """
        Colorizes all the shape nodes below this transform.

        :key side: int
        :key: colorIndex: int
        :key: colorRGB: Tuple[float, float, float]
        :rtype: None
        """

        # Iterate through shapes
        #
        for shape in self.iterShapes():

            shapeutils.colorizeShape(shape.object(), **kwargs)
    # endregion
