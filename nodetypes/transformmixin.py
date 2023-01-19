from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.naming import namingutils
from dcc.python import stringutils
from dcc.maya.libs import shapeutils, transformutils
from . import dagmixin
from .. import mpyattribute

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
        This overload supports the use of transform preservation when changing parents.

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

    def translation(self, space=om.MSpace.kTransform):
        """
        Returns the transform's translation component.

        :type space: int
        :rtype: om.MVector
        """

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

    def eulerRotation(self):
        """
        Returns the transform's rotation component.

        :rtype: om.MEulerRotation
        """

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

    def scale(self):
        """
        Returns the transform's scale component.

        :rtype: List[float, float, float]
        """

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

    def resetPivots(self):
        """
        Resets all the transform's pivot components.

        :rtype: None
        """

        transformutils.resetPivots(self.dagPath())

    def matrix(self, asTransformationMatrix=False):
        """
        Returns the local transformation matrix for this transform.

        :type asTransformationMatrix: bool
        :rtype: Union[om.MMatrix, om.MTransformationMatrix]
        """

        return transformutils.getMatrix(self.dagPath(), asTransformationMatrix=asTransformationMatrix)

    def setMatrix(self, matrix, skipTranslate=False, skipRotate=False, skipScale=False):
        """
        Updates the local transformation matrix for this transform.

        :type matrix: om.MMatrix
        :type skipTranslate: bool
        :type skipRotate: bool
        :type skipScale: bool
        :rtype: None
        """

        transformutils.applyTransformMatrix(
            self.dagPath(),
            matrix,
            skipTranslate=skipTranslate,
            skipRotate=skipRotate,
            skipScale=skipScale
        )

    def resetMatrix(self):
        """
        Resets all the transform components back to zero.

        :rtype: None
        """

        self.resetTranslation()
        self.resetPreEulerRotation()
        self.resetEulerRotation()
        self.resetScale()

    def parentMatrix(self):
        """
        Returns the parent matrix for this transform.

        :rtype: om.MMatrix
        """

        return transformutils.getParentMatrix(self.dagPath())

    def parentInverseMatrix(self):
        """
        Returns the parent inverse-matrix for this transform.

        :rtype: om.MMatrix
        """

        return self.parentMatrix().inverse()

    def worldMatrix(self):
        """
        Returns the world matrix for this transform.

        :rtype: om.MMatrix
        """

        return transformutils.getWorldMatrix(self.dagPath())

    def worldInverseMatrix(self):
        """
        Returns the world inverse-matrix for this transform.

        :rtype: om.MMatrix
        """

        return self.worldMatrix().inverse()

    def keyTransform(self):
        """
        Keys just the transform component attributes.

        :rtype: None
        """

        self.keyAttrs(
            [
                'translateX', 'translateY', 'translateZ',
                'rotateX', 'rotateY', 'rotateZ',
                'scaleX', 'scaleY', 'scaleZ'
            ]
        )

    def alignToTransform(self, transform, startFrame=0, endFrame=1, step=1):
        """
        Aligns the transform to the other transform over a period of time.

        :type transform: TransformMixin
        :type startFrame: int
        :type endFrame: int
        :type step: int
        :rtype: None
        """

        # Iterate through time range
        #
        for i in range(startFrame, endFrame + 1, step):

            self.setCurrentTime(i)
            self.copyTransform(transform)
            self.keyTransform()

    def copyTransform(self, transform):
        """
        Copies the transform components from the supplied node onto this one.

        :type transform: TransformMixin
        :rtype: None
        """

        transformutils.copyTransform(self.dagPath(), transform.dagPath())

    def resetTransform(self):
        """
        Resets all the channel-box plugs back to their default value.

        :rtype: None
        """

        for plug in self.iterPlugs(channelBox=True):

            self.resetAttr(plug)

    def freezeTransform(self, includeTranslate=True, includeRotate=True, includeScale=False):
        """
        Pushes the transform's local matrix into the parent offset matrix.

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
        Pushes the transform's parent offset matrix into the local matrix.

        :rtype: None
        """

        transformutils.unfreezeTransform(self.dagPath())

    def addShape(self, shape, **kwargs):
        """
        Adds the specified shape to this transform node.
        See the shapes directory for a list of accepts shapes.

        :type shape: str
        :rtype: list[om.MObject]
        """

        filePath = self.scene.getShapeTemplate(shape)
        return shapeutils.applyShapeTemplate(filePath, parent=self.object(), **kwargs)

    def addLocator(self, *args, **kwargs):
        """
        Adds a locator shape to this transform.

        :key localPosition: list[float, float, float]
        :key localScale: list[float, float, float]
        :rtype: mpynode.nodetypes.shapemixin.ShapeMixin
        """

        # Create point helper shape
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

    def addPointHelper(self, *args, **kwargs):
        """
        Adds a point helper shape to this transform.

        :key size: float
        :key side: int
        :key localPosition: list[float, float, float]
        :key localRotate: list[float, float, float]
        :key localScale: list[float, float, float]
        :rtype: mpynode.nodetypes.shapemixin.ShapeMixin
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

        return pointHelper

    def removeShapes(self):
        """
        Removes all the shapes underneath this transform.
        This method is undoable!

        :rtype: None
        """

        # Iterate through shapes
        #
        for shape in self.iterShapes():

            shape.delete()

    def colorizeShapes(self, **kwargs):
        """
        Colorizes all the shape nodes below this transform.

        :key side: int
        :key: colorIndex: int
        :key: colorRGB: list[float, float, float]
        :rtype: None
        """

        # Iterate through shapes
        #
        for shape in self.iterShapes():

            shapeutils.colorizeShape(shape.object(), **kwargs)

    def addGlobalScaleAttribute(self):
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
        name = self.fullPathName()

        mc.addAttr('%s.globalScale' % name, attributeType='float', defaultValue=1.0)
        mc.connectAttr('%s.globalScale' % name, '%s.scaleX' % name)
        mc.connectAttr('%s.globalScale' % name, '%s.scaleY' % name)
        mc.connectAttr('%s.globalScale' % name, '%s.scaleZ' % name)

        # Hide scale attributes
        #
        self.hideAttrs(['scaleX', 'scaleY', 'scaleZ'])

    def prepareChannelBoxForAnimation(self):
        """
        Prepares the channel box for animation.
        Right now this means hiding the visibility attribute and restoring the rotate order for animators.

        :rtype: None
        """

        self.hideAttr('visibility')
        self.showAttr('rotateOrder')

    def isController(self):
        """
        Checks if this transform node has been tagged as a controller.

        :rtype: bool
        """

        return self.controllerTag() is not None

    def controllerTag(self):
        """
        Returns the controller tag for this transform node.
        This method will raise a type error if multiple tags are found!

        :rtype: mpy.nodetypes.controllermixin.ControllerMixin
        """

        # Collect all controller tags
        #
        plug = self.findPlug('message')

        destinations = plug.destinations()
        numDestinations = len(destinations)

        if numDestinations == 0:

            return None

        # Iterate through destinations
        #
        for destination in destinations:

            # Check if this is a controller node
            #
            node = destination.node()
            plugName = destination.partialName(useLongNames=True)

            if node.hasFn(om.MFn.kControllerTag) and plugName == 'controllerObject':

                return self.scene(node)

            else:

                continue

        return None

    def tagAsController(self, **kwargs):
        """
        Tags this transform node as a controller.
        If this transform is already tagged then that controller will be returned.

        :rtype: mpy.nodetypes.controllermixin.ControllerMixin
        """

        # Check for redundancy
        #
        controllerTag = self.controllerTag()

        if controllerTag is not None:

            return controllerTag

        # Create new controller tag
        #
        controllerTag = self.scene.createNode('controller', name='{nodeName}_tag'.format(nodeName=self.name()))
        controllerTag.controllerObject = self.object()

        # Check if parent was supplied
        #
        parent = kwargs.get('parent', None)

        if parent is not None:

            controllerTag.parent = parent.object()

        # Check if child controller were supplied
        #
        children = kwargs.get('children', None)

        if children is not None:

            controllerTag.children = [child.object() for child in children]

        return controllerTag

    def findOppositeTransform(self):
        """
        Finds the transform opposite to this one.
        If no opposite is found then this transform is returned instead!

        :rtype: TransformMixin
        """

        name = self.name(includeNamespace=True)
        mirrorName = namingutils.mirrorName(name)

        if mc.objExists(mirrorName):

            return self.scene(mirrorName)

        else:

            return self

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

        otherTransform = self.findOppositeTransform()
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

    def mirrorTransform(self, pull=False):
        """
        Mirrors this transform to the opposite node.

        :type pull: bool
        :rtype: None
        """

        # Get opposite transform
        #
        otherTransform = self.findOppositeTransform()

        if pull:

            # Iterate through channel-box plugs
            #
            for plug in otherTransform.iterPlugs(channelBox=True):

                # Get mirror flag for plug
                #
                plugName = plug.partialName(useLongNames=True)
                mirrorFlag = 'mirror{name}'.format(name=stringutils.pascalize(plugName))

                mirrorEnabled = self.userProperties.get(mirrorFlag, False)

                # Inverse value and update other node
                #
                value = otherTransform.getAttr(plug)
                value *= -1.0 if mirrorEnabled else 1.0

                self.setAttr(plugName, value)

        else:

            # Iterate through channel-box plugs
            #
            for plug in self.iterPlugs(channelBox=True):

                # Get mirror flag for plug
                #
                plugName = plug.partialName(useLongNames=True)
                mirrorFlag = 'mirror{name}'.format(name=stringutils.pascalize(plugName))

                mirrorEnabled = self.userProperties.get(mirrorFlag, False)

                # Inverse value and update other node
                #
                value = self.getAttr(plug)
                value *= -1.0 if mirrorEnabled else 1.0

                otherTransform.setAttr(plugName, value)

    def mirrorAnimation(self, pull=False):
        """
        Mirrors this transform's animation to the opposite node.

        :type pull: bool
        :rtype: None
        """

        pass

    def constraintCount(self):
        """
        Counts the number of constraints connected to this transform.

        :rtype: int
        """

        return len(self.constraints())

    def hasConstraints(self):
        """
        Checks if this transform has any constraints.

        :rtype: bool
        """

        return self.constraintCount() > 0

    def constraints(self, apiType=om.MFn.kConstraint):
        """
        Retrieves a list of constraints that are driving this transform.

        :type apiType: int
        :rtype: List[mpy.nodetypes.constraintmixin.ConstraintMixin]
        """

        return self.dependsOn(apiType=apiType)

    def addConstraint(self, typeName, targets, **kwargs):
        """
        Adds a constraint node to this transform.
        Any constrained attributes can be skipped by supplying them as keyword arguments: skipTranslateX, etc

        :type typeName: str
        :type targets: List[TransformMixin]
        :key maintainOffset: bool
        :rtype: mpy.nodetypes.constraintmixin.ConstraintMixin
        """

        # Create constraint and assign targets
        #
        constraint = self.scene.createNode(typeName)
        constraint.setConstraintObject(self, **kwargs)
        constraint.addTargets(targets)

        return constraint
    # endregion
