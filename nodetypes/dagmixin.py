from maya import cmds as mc
from maya.api import OpenMaya as om
from collections import deque
from dcc.maya.libs import dagutils

from . import containerbasemixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DagMixin(containerbasemixin.ContainerBaseMixin):
    """
    Overload of NodeMixin used to interface with DAG nodes inside the scene file.
    """

    __apitype__ = om.MFn.kDagNode

    visibility = mpyattribute.MPyAttribute('visibility')
    template = mpyattribute.MPyAttribute('template')
    ghosting = mpyattribute.MPyAttribute('ghosting')
    objectColorRGB = mpyattribute.MPyAttribute('objectColorRGB')
    wireColorRGB = mpyattribute.MPyAttribute('wireColorRGB')
    useObjectColor = mpyattribute.MPyAttribute('useObjectColor')
    objectColor = mpyattribute.MPyAttribute('objectColor')
    hiddenInOutliner = mpyattribute.MPyAttribute('hiddenInOutliner')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(DagMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        """
        Private method used to return either an indexed plug or node.

        :type key: Union[str, int]
        :rtype: Union[om.MPlug, mpynode.MPyNode]
        """

        # Check key type
        #
        if isinstance(key, int):

            return self.child(key)

        else:

            return super(DagMixin).__getitem__(key)

    def __reduce__(self):
        """
        The cPickle module uses the __reduce__() method to instruct it on how to simplify the class into a string.

        :return: Tuple containing the class and constructor arguments.
        :rtype: tuple[type, tuple[str]]
        """

        return self.nodeClass(), (self.fullPathName(),)

    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnDagNode
        """

        return self.__functionset__.__call__(self.dagPath())

    def dagPath(self):
        """
        Returns a dag path to this object.

        :rtype: om.MDagPath
        """

        return om.MDagPath.getAPathTo(self.object())

    def instanceNumber(self):
        """
        Returns the instance number of this object.

        :rtype: int
        """

        return self.dagPath().instanceNumber()

    def isInstanced(self):
        """
        Evaluates whether this object is instanced.

        :rtype: bool
        """

        return self.dagPath().isInstanced()

    def isValid(self):
        """
        Evaluates whether this object is still valid.

        :rtype: bool
        """

        return self.dagPath().isValid()

    def isVisible(self):
        """
        Evaluates whether this object is visible in the viewport.

        :rtype: bool
        """

        return self.dagPath().isVisible()

    @property
    def isIntermediateObject(self):
        """
        Getter method that evaluates if this is an intermediate object.

        :rtype: bool
        """

        return self.functionSet().isIntermediateObject

    def inclusiveMatrix(self):
        """
        Returns the inclusive matrix of this dag node.

        :type: om.MMatrix
        """

        return self.dagPath().inclusiveMatrix()

    def inclusiveMatrixInverse(self):
        """
        Returns the inclusive inverse matrix of this dag node.

        :type: om.MMatrix
        """

        return self.dagPath().inclusiveMatrixInverse()

    def exclusiveMatrix(self):
        """
        Returns the exclusive matrix of this dag node.

        :type: om.MMatrix
        """

        return self.dagPath().exclusiveMatrix()

    def exclusiveMatrixInverse(self):
        """
        Returns the exclusive inverse matrix of this dag node.

        :type: om.MMatrix
        """

        return self.dagPath().exclusiveMatrixInverse()

    def isSelected(self):
        """
        Evaluates whether this object is currently selected.

        :rtype: bool
        """

        return om.MGlobal.getActiveSelectionList().hasItemPartly(self.dagPath(), self.component())

    def fullPathName(self):
        """
        Returns the full path name that represents this object.

        :rtype: str
        """

        return self.dagPath().fullPathName()

    def partialPathName(self):
        """
        Returns the shortest possible path name that can be safely used to lookup this object.

        :rtype: str
        """

        return self.dagPath().partialPathName()

    def show(self):
        """
        Un-hides the node inside the viewport.

        :rtype: None
        """

        self.visibility = True

    def hide(self):
        """
        Hides the node inside the viewport.

        :rtype: None
        """

        self.visibility = False

    def component(self):
        """
        Returns the active component selection related to this instance.
        Be aware that running 'getRichSelection' will raise runtime errors when the selection list is empty!

        :rtype: om.MObject
        """

        # Check api type
        #
        component = om.MObject.kNullObj

        if not self.hasFn(om.MFn.kShape):

            log.warning('Cannot get component from "%s" api type!' % self.apiTypeStr)
            return component

        # Get active selection
        # Unfortunately the rich selection method will raise a runtime error if the selection is empty
        # So we have to wrap this in a try/catch in order to preserve weighted component data
        #
        selection = None

        try:

            selection = om.MGlobal.getRichSelection().getSelection()

        except RuntimeError as exception:

            log.debug(exception)
            selection = om.MGlobal.getActiveSelectionList()

        # Initialize selection iterator
        #
        iterSelection = om.MItSelectionList(selection, om.MFn.kComponent)

        while not iterSelection.isDone():

            # Get the current selected item and component
            #
            dagPath, component = iterSelection.getComponent()

            if dagPath.node() == self.object() and not component.isNull():

                log.debug('Detected %s component on %s.' % (component.apiTypeStr, dagPath.partialPathName()))
                break

            else:

                log.info('Skipping invalid component selection on %s.' % dagPath.partialPathName())

            # Go to next item
            #
            iterSelection.next()

        return component

    def parent(self):
        """
        Returns the parent of this instance.

        :rtype: DagMixin
        """

        # Check if dag node has any parents
        #
        fnDagNode = self.functionSet()
        parentCount = fnDagNode.parentCount()

        if parentCount == 0:

            return None

        else:

            return self.pyFactory(fnDagNode.parent(self.instanceNumber()))

    def hasParent(self):
        """
        Evaluates whether this node has a parent.

        :rtype: bool
        """

        return self.functionSet().parentCount() > 0

    def setParent(self, parent):
        """
        Updates the parent of this instance.

        :type parent: DagMixin
        :rtype: None
        """

        # Check if parent is valid
        #
        if not parent.hasFn(om.MFn.kDagNode):

            return

        # Check for redundancy
        #
        if parent == self.parent():

            return

        # Setup dag modifier
        #
        dagModifer = om.MDagModifier()
        dagModifer.reparentNode(self.object(), parent.object())
        dagModifer.doIt()

    def iterParents(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that can iterate over all of the parents relative to this node.

        :rtype: iter
        """

        # Iterate through parents
        #
        current = self.parent()

        while current is not None:

            # Check parent type
            #
            if current.hasFn(apiType):

                yield current
                current = current.parent()

            else:

                break

    def topLevelParent(self):
        """
        Returns the top level parent relative to this node.
        If this node is already the top most parent then itself is returned.

        :rtype: DagMixin
        """

        parents = list(self.iterParents())
        numParents = len(parents)

        if numParents == 0:

            return self

        else:

            return parents[-1]

    def child(self, index):
        """
        Returns an indexed child object.

        :type index: int
        :rtype: mpynode.MPyNode
        """

        return self.pyFactory(self.functionSet().child(index))

    def childCount(self):
        """
        Evaluates the number of children below this object.

        :rtype: int
        """

        return self.dagPath().childCount()

    def iterChildren(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that yields all the children below this object.
        An optional api type can be supplied to narrow down the children.

        :type apiType: int
        :rtype: iter
        """

        for child in dagutils.iterChildren(self.dagPath(), apiType=apiType):

            yield self.pyFactory(child)

    def iterShapes(self):
        """
        Returns a generator that yields all of the shapes below this object.

        :rtype: iter
        """

        return self.iterChildren(apiType=om.MFn.kShape)

    def iterDescendants(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that yields all of the descendants below this object.
        An optional api type can be supplied to narrow down the children.

        :type apiType: int
        :rtype: iter
        """

        # Iterate through queue
        #
        queue = deque(self.children(apiType=apiType))

        while len(queue) > 0:

            # Yield child node
            #
            child = queue.popleft()
            yield child

            # Collect descendants
            #
            queue.extend(child.children(apiType=apiType))

    def children(self, apiType=om.MFn.kDagNode):
        """
        Returns all of the children belonging to this object.

        :type apiType: int
        :rtype: list[DagMixin]
        """

        return list(self.iterChildren(apiType=apiType))

    def shape(self, index=0):
        """
        Returns an indexed shape object.

        :type index: int
        :rtype: mpynode.nodetypes.shapemixin.ShapeMixin
        """

        # Inspect number of shapes
        #
        if 0 <= index < self.numberOfShapesDirectlyBelow():

            return self.shapes()[index]

        else:

            return None

    def shapes(self):
        """
        Returns all of the shapes below this object.

        :rtype: list[mpynode.nodetypes.shapemixin.ShapeMixin]
        """

        return [x for x in self.iterShapes() if not x.isIntermediateObject]

    def numberOfShapesDirectlyBelow(self):
        """
        Method used to check the number of shapes below this object.

        :rtype: int
        """

        return self.dagPath().numberOfShapesDirectlyBelow()

    def hasShape(self):
        """
        Method used to determine if this transform has any shape nodes.

        :rtype: bool
        """

        return self.numberOfShapesDirectlyBelow() > 0

    def intermediateObjects(self):
        """
        Method used to collect all intermediate objects parented to this object.

        :rtype: list[DagMixin]
        """

        return [x for x in self.iterShapes() if x.isIntermediateObject]

    def descendants(self):
        """
        Returns a list of descendants relative to this node.

        :rtype: list[DagMixin]
        """

        return list(self.iterDescendants())
