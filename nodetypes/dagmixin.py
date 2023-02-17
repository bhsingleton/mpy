from maya import cmds as mc
from maya.api import OpenMaya as om
from collections import deque
from six import integer_types, string_types
from dcc.maya.libs import dagutils
from . import containerbasemixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DagMixin(containerbasemixin.ContainerBaseMixin):
    """
    Overload of `ContainerBaseMixin` that interfaces with DAG nodes.
    """

    # region Attributes
    visibility = mpyattribute.MPyAttribute('visibility')
    template = mpyattribute.MPyAttribute('template')
    ghosting = mpyattribute.MPyAttribute('ghosting')
    useObjectColor = mpyattribute.MPyAttribute('useObjectColor')
    objectColor = mpyattribute.MPyAttribute('objectColor')
    objectColorRGB = mpyattribute.MPyAttribute('objectColorRGB')
    wireColorRGB = mpyattribute.MPyAttribute('wireColorRGB')
    hiddenInOutliner = mpyattribute.MPyAttribute('hiddenInOutliner')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kDagNode

    def __str__(self):
        """
        Private method that stringifies this node.

        :rtype: str
        """

        return self.partialPathName()

    def __getitem__(self, key):
        """
        Private method used to return either an indexed plug or node.

        :type key: Union[str, int]
        :rtype: Union[om.MPlug, mpynode.MPyNode]
        """

        # Check key type
        #
        if isinstance(key, integer_types):

            return self.child(key)

        else:

            return super(DagMixin, self).__getitem__(key)

    def __reduce__(self):
        """
        The cPickle module uses the __reduce__() method to instruct it on how to simplify this class into a string.

        :return: Tuple containing the class and constructor arguments.
        :rtype: Tuple[type, Tuple[str]]
        """

        return self.nodeClass(), (self.fullPathName(),)
    # endregion

    # region Methods
    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnDagNode
        """

        return self.__function_set__.__call__(self.dagPath())

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

    def select(self, replace=False):
        """
        Method used to select this instance.

        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        selection = om.MSelectionList()

        if not replace:

            selection = om.MGlobal.getActiveSelectionList()

        # Reset active selection
        #
        selection.add(self.dagPath())
        om.MGlobal.setActiveSelectionList(selection)

    def deselect(self):
        """
        Method used to deselect this instance.

        :rtype: None
        """

        # Get active selection
        #
        selection = om.MGlobal.getActiveSelectionList()

        if self.isSelected():

            selection.remove(self.dagPath())

        # Reset active selection
        #
        om.MGlobal.setActiveSelectionList(selection)

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
        Returns the active component selection from this node.

        :rtype: om.MObject
        """

        components = [component for (dagPath, component) in dagutils.iterActiveComponentSelection() if self == dagPath]
        numComponents = len(components)

        if numComponents == 0:

            return om.MObject.kNullObj

        elif numComponents == 1:

            return components[0]

        else:

            raise TypeError('component() expects a unique component selection (%s found)!' % numComponents)

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: Union[DagMixin, None]
        """

        return self.scene(dagutils.getParent(self.object()))

    def hasParent(self):
        """
        Evaluates whether this node has a parent.

        :rtype: bool
        """

        return not self.functionSet().parent(0).hasFn(om.MFn.kWorld)

    def setParent(self, parent):
        """
        Updates the parent for this node.

        :type parent: Union[None, str, om.MObject, DagMixin]
        :rtype: None
        """

        # Redundancy check
        #
        parent = self.scene(parent)

        if self.parent() == parent:

            return

        # Execute dag modifier
        #
        if parent.hasFn(om.MFn.kDagNode):

            dagutils.parentNode(self.object(), parent.object())

        else:

            raise TypeError('setParent() expects a valid dag node (%s given)!' % parent.apiTypeStr)

    def iterAncestors(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that yields the parents from this node.

        :rtype: Iterator[DagMixin]
        """

        return map(self.scene, dagutils.iterAncestors(self.object(), apiType=apiType))

    def ancestors(self):
        """
        Returns a list of parents from this node.

        :rtype: List[DagMixin]
        """

        return list(self.iterAncestors())

    def topLevelParent(self):
        """
        Returns the top level parent relative to this node.
        If this node is already the top most parent then itself is returned.

        :rtype: DagMixin
        """

        ancestors = list(self.iterAncestors())
        numAncestors = len(ancestors)

        if numAncestors == 0:

            return self

        else:

            return ancestors[-1]

    def trace(self):
        """
        Returns a generator that yields the parents leading to this node.

        :rtype: Iterator[DagMixin]
        """

        return map(self.scene, dagutils.traceHierarchy(self.object()))

    def child(self, index):
        """
        Returns an indexed child node.

        :type index: int
        :rtype: DagMixin
        """

        # Check if index is in range
        #
        childCount = self.childCount()

        if 0 <= index < childCount:

            return self.scene(self.functionSet().child(index))

        else:

            raise IndexError('child() index out of range!')

    def childCount(self):
        """
        Evaluates the number of children below this object.

        :rtype: int
        """

        return self.dagPath().childCount()

    def iterChildren(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that yields children from this node.
        An optional api type can be supplied to narrow down the children.

        :type apiType: int
        :rtype: Iterator[DagMixin]
        """

        return map(self.scene, dagutils.iterChildren(self.dagPath(), apiType=apiType))

    def iterShapes(self):
        """
        Returns a generator that yields shapes from this node.

        :rtype: Iterator[DagMixin]
        """

        return self.iterChildren(apiType=om.MFn.kShape)

    def iterDescendants(self, apiType=om.MFn.kDagNode):
        """
        Returns a generator that yields the descendants from this node.
        An optional api type can be supplied to narrow down the descendants.

        :type apiType: int
        :rtype: Iterator[DagMixin]
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
        Returns a list of the children from this node.

        :type apiType: int
        :rtype: List[DagMixin]
        """

        return list(self.iterChildren(apiType=apiType))

    def shape(self, index=0):
        """
        Returns an indexed shape from this node.

        :type index: int
        :rtype: DagMixin
        """

        # Inspect number of shapes
        #
        if 0 <= index < self.numberOfShapesDirectlyBelow():

            return self.shapes()[index]

        else:

            return None

    def shapes(self):
        """
        Returns a list of the shapes from this node.

        :rtype: List[DagMixin]
        """

        return [x for x in self.iterShapes() if not x.isIntermediateObject]

    def numberOfShapesDirectlyBelow(self):
        """
        Evaluates the number of shapes from this node.

        :rtype: int
        """

        return self.dagPath().numberOfShapesDirectlyBelow()

    def hasShape(self):
        """
        Evaluates if this node has any shapes.

        :rtype: bool
        """

        return self.numberOfShapesDirectlyBelow() > 0

    def intermediateObjects(self):
        """
        Returns a list of intermediate objects from this node.

        :rtype: list[DagMixin]
        """

        return [x for x in self.iterShapes() if x.isIntermediateObject]

    def descendants(self):
        """
        Returns a list of descendants from this node.

        :rtype: list[DagMixin]
        """

        return list(self.iterDescendants())
    # endregion
