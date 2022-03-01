import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.maya.libs import shapeutils, transformutils

from . import dagmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransformMixin(dagmixin.DagMixin):
    """
    Overload of DagMixin class used to interface with transform nodes.
    """

    __apitype__ = (om.MFn.kTransform, om.MFn.kPluginTransformNode)

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

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(TransformMixin, self).__init__(*args, **kwargs)

    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnTransform
        """

        return super(TransformMixin, self).functionSet()

    def translation(self, space=om.MSpace.kTransform, context=om.MDGContext.kNormal):
        """
        Returns the transform's translation component.
        A custom MDGContext can be supplied to sample the translation at a different time.

        :type space: int
        :type context: om.MDGContext
        :rtype: om.MVector
        """

        return transformutils.getTranslation(self.dagPath(), space=space, context=context)

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
        Resets the translation component back to zero.

        :rtype: None
        """

        transformutils.resetTranslation(self.dagPath())

    def rotateOrder(self, context=om.MDGContext.kNormal):
        """
        Returns the rotation order for this component.

        :type context: om.MDGContext
        :rtype: int
        """

        return transformutils.getRotationOrder(self.dagPath(), context=context)

    def eulerRotation(self, context=om.MDGContext.kNormal):
        """
        Returns the transform's rotation component.
        A custom MDGContext can be supplied to sample the rotation at a different time.

        :type context: om.MDGContext
        :rtype: om.MEulerRotation
        """

        transformutils.getEulerRotation(self.dagPath(), context=context)

    def setEulerRotation(self, eulerRotation):
        """
        Updates the transform's rotation component

        :type eulerRotation: om.MEulerRotation
        :rtype: None
        """

        transformutils.setEulerRotation(self.dagPath(), eulerRotation)

    def resetEulerRotation(self):
        """
        Resets the rotation component back to zero.

        :rtype: None
        """

        transformutils.resetEulerRotation(self.dagPath())

    def scale(self, context=om.MDGContext.kNormal):
        """
        Returns the transform's scale component.

        :type context: om.MDGContext
        :rtype: list[float, float, float]
        """

        return transformutils.getScale(self.dagPath(), context=context)

    def setScale(self, scale):
        """
        Updates the transform's scale component

        :type scale: list[float, float, float]
        :rtype: None
        """

        transformutils.setScale(self.dagPath(), scale)

    def resetScale(self):
        """
        Resets the scale component back to one.

        :rtype: None
        """

        transformutils.resetScale(self.dagPath())

    def resetPivots(self):
        """
        Resets all of the transform's pivot components.

        :rtype: None
        """

        transformutils.resetPivots(self.dagPath())

    def matrix(self):
        """
        Returns the local transformation matrix for this transform.

        :rtype: om.MMatrix
        """

        return self.getAttr('matrix')

    def setMatrix(self, matrix):
        """
        Updates the local transformation matrix for this transform.

        :type matrix: om.MMatrix
        :rtype: None
        """

        # Decompose transform matrix
        #
        translation, rotation, scale = transformutils.decomposeTransformMatrix(matrix)

        # Set transform components
        #
        self.setTranslation(translation)
        self.setEulerRotation(rotation)
        self.setScale(scale)

    def resetMatrix(self):
        """
        Resets all of transform's components.

        :rtype: None
        """

        self.resetTranslation()
        self.resetEulerRotation()
        self.resetScale()

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

    def mirrorTransform(self):
        """
        Mirrors the transform components to this controller's sibling.

        :rtype: None
        """

        # Check if this is a controller
        #
        if not self.isController():

            return

        # Get controller sibling
        #
        controllerTag = self.controllerTag()
        sibling = controllerTag.sibling()

        if sibling is None:

            return

        # Mirror translation
        #
        translation = self.translation()
        translation.x *= (-1.0 * controllerTag.mirrorTranslateX)
        translation.y *= (-1.0 * controllerTag.mirrorTranslateY)
        translation.z *= (-1.0 * controllerTag.mirrorTranslateZ)

        transformutils.setTranslation(sibling.dagPath(), translation)

        # Mirror rotation
        #
        eulerRotation = self.eulerRotation()
        eulerRotation.x *= (-1.0 * controllerTag.mirrorRotateX)
        eulerRotation.y *= (-1.0 * controllerTag.mirrorRotateY)
        eulerRotation.z *= (-1.0 * controllerTag.mirrorRotateZ)

        transformutils.setEulerRotation(sibling.dagPath(), eulerRotation)

    def freezeTransform(self, includeTranslate=True, includeRotate=True, includeScale=True):
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

        filePath = self.pyFactory.getShapeTemplate(shape)
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
        name = '{name}Shape'.format(name=self.displayName())
        locator = self.pyFactory.createNode('locator', name=name, parent=self)

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
        name = '{name}Shape'.format(name=self.displayName())
        pointHelper = self.pyFactory.createNode('pointHelper', name=name, parent=self)

        # Check if any shapes were supplied
        #
        numArgs = len(args)

        if numArgs > 0:

            # Disable all default shapes
            #
            for attribute in pointHelper.iterAttr(category='Drawable'):

                plug = om.MPlug(pointHelper.object(), attribute)
                plug.setBool(False)

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
        Removes all of the shapes below this transform.
        This method is undoable!

        :rtype: None
        """

        # Iterate through shapes
        #
        for shape in self.iterShapes():

            shape.delete()

    def colorizeShapes(self, **kwargs):
        """
        Colorizes all of the shape nodes below this transform.

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
        Once done all of the scale attributes will be hidden.

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

        :rtype: mpynode.nodetypes.controllermixin.ControllerMixin
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

                return self.pyFactory(node)

            else:

                continue

        return None

    def tagAsController(self, **kwargs):
        """
        Tags this transform node as a controller.
        If this transform is already tagged then that controller will be returned.

        :rtype: mpynode.nodetypes.controllermixin.ControllerMixin
        """

        # Check for redundancy
        #
        controllerTag = self.controllerTag()

        if controllerTag is not None:

            return controllerTag

        # Create new controller tag
        #
        controllerTag = self.pyFactory.createNode('controller', name='{nodeName}_tag'.format(nodeName=self.displayName()))

        controllerTag.controllerObject = self.object()
        controllerTag.side = kwargs.get('side', 2)
        controllerTag.type = kwargs.get('type', 0)
        controllerTag.otherType = kwargs.get('otherType', '')

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
        :rtype: list[mpynode.nodetypes.constraintmixin.ConstraintMixin]
        """

        return self.dependsOn(apiType=apiType)

    def addConstraint(self, typeName, targets, **kwargs):
        """
        Adds a constraint node to this transform.
        Any constrained attributes can be skipped by supplying them as keyword arguments: skipTranslateX

        :type typeName: str
        :type targets: list[TransformMixin]
        :key maintainOffset: bool
        :rtype: mpynode.nodetypes.constraintmixin.ConstraintMixin
        """

        # Create constraint and assign targets
        #
        constraint = self.pyFactory.createNode(typeName)
        constraint.setConstraintObject(self, **kwargs)
        constraint.addTargets(targets)

        return constraint
