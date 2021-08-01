"""
Skin cluster mixin used to manipulate skin weights directly.
As far as maximum number of influence per-vertex go please see the following:
For SM4 (D3D10) and SM5 (D3D11) the max influence is 8.
For ES2 (Mobile) max influence is 4.
Anything prior to UE4 will also be capped at 4 influences.
"""
import maya.cmds as mc
import maya.api.OpenMaya as om
import os

from copy import deepcopy
from numpy import isclose
from collections.abc import MutableSequence, KeysView, ValuesView

from . import deformermixin
from .. import mpyattribute
from ..decorators import undo
from ..utilities.pyutils import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InfluenceObjects(MutableSequence):
    """
    Overload of MutableSequence used to store influence objects from a skin cluster.
    """

    __slots__ = ('__skin__', '__influences__',)

    def __init__(self, skinCluster):
        """
        Dunderscore method called after a new instance has been created.

        :type skinCluster: SkinMixin
        :rtype: None
        """

        # Call parent method
        #
        super(InfluenceObjects, self).__init__()

        # Declare class variables
        #
        self.__skin__ = skinCluster.weakReference()
        self.__influences__ = []

        # Collect influence objects
        #
        for index, influenceObject in skinCluster.iterInfluenceObjects():

            self.__setitem__(index, influenceObject)

    def __getitem__(self, item):
        """
        Dunderscore method used to retrieve an indexed item from this list.
        Based on the index type there are different return operations:
            Supplying a node name will cause this method to return the associated influence ID.
            Supplying an influence ID will return the associated dag node.
            Supplying a list will return all of the indexed items being requested.

        :type item: Union[int, str]
        :rtype: mpynode.nodetypes.transformmmixin.TransformMixin
        """

        # Check item type
        #
        if isinstance(item, int):

            # Check if index is within range
            #
            if 0 <= item < self.__len__():

                # Retrieve weak reference from list
                #
                influence = self.__influences__[item]

                if influence is not None:

                    return influence()

                else:

                    return None

            else:

                log.debug('Unable to access out of range influence ID!')
                return None

        elif isinstance(item, string_types):

            # Perform index lookup for string name
            #
            return self.index(item)

        elif isinstance(item, (list, tuple)):

            # Generate return list from items
            #
            return [self.__getitem__(x) for x in item]

        else:

            raise TypeError('__getitem__() expects either an int or string (%s given)!' % type(item).__name__)

    def __setitem__(self, index, item):
        """
        Dunderscore method used to commit and influence to the supplied index.

        :type index: int
        :type item: Union[om.MObject, None]
        :rtype: None
        """

        # Check index type
        #
        if not isinstance(index, int):

            raise TypeError('__setitem__() expects an int (%s given)!' % type(index).__name__)

        # Check if list requires expanding
        #
        numItems = len(self.__influences__)

        if index >= numItems:

            self.__fill__(index)

        # Assign item to list
        #
        if item is not None:

            self.__influences__[index] = SkinMixin.pyFactory(item).weakReference()

        else:

            self.__influences__[index] = None

    def __delitem__(self, index):
        """
        Dunderscore method called whenever the user attempts to delete an item from this list.
        We don't wanna pop the entry since this will offset all influences!

        :type index: int
        :rtype: None
        """

        # Check if index is within range
        #
        if 0 <= index < self.__len__():

            self.__influences__[index] = None

        else:

            log.warning('Unable to remove out of range influence!')
            return

    def __contains__(self, item):
        """
        Dunderscore method used to determine if the supplied item exists inside this list.

        :type item: Union[str, int, om.MObject]
        :rtype: bool
        """

        # Check item type
        #
        if isinstance(item, int):

            return True if 0 <= item < self.__len__() else False

        elif item is not None:

            return self.index(item) is not None

        else:

            return False

    def __iter__(self):
        """
        Generator method used to iterate through all of the influences associated with this instance.
        Any null influences will also be yielded!

        :rtype: iter
        """

        for influence in self.__influences__:

            yield influence

    def __len__(self):
        """
        Method used to determine the number of influences belonging to this instance.
        This will include null influences as well!

        :rtype: int
        """

        return len(self.__influences__)

    def __fill__(self, index):
        """
        Fills the list with null values to the specified index while respecting pre-existing indices.

        :type index: int
        :rtype: None
        """

        # Get length of list
        #
        numItems = self.__len__()

        if index >= numItems:

            # Iterate from length to index
            #
            log.debug('Filling influence list from %s to %s.' % (numItems, index))

            diff = (index + 1) - numItems
            self.__influences__.extend([None] * diff)

        else:

            log.warning('Unable to fill influence list with null values!')

        # Return reference self
        #
        return self

    def iteritems(self):
        """
        Generator method used to iterate through all of the influences with their associated index.
        Any null influences will also be yielded!

        :rtype: iter
        """

        # Enumerate items
        #
        for (influenceId, influence) in enumerate(self.__influences__):

            # Check for none type
            #
            if influence is not None:

                yield influenceId, influence()

            else:

                yield influenceId, influence

    def append(self, item):
        """
        Dunderscore method used to add a value onto the end of this list.

        :type item: om.MObject
        :rtype: None
        """

        self.__setitem__(self.__len__(), item)

    def extend(self, items):
        """
        Dunderscore method used to add a sequence of item onto this list.

        :type items: Union[list, tuple, om.MObjectArray]
        :rtype: None
        """

        # Check index type
        #
        if not isinstance(items, (list, tuple, om.MObjectArray)):

            raise TypeError('insert() expects a list (%s given)!' % type(items).__name__)

        # Append items to list
        #
        for item in items:

            self.append(item)

    def insert(self, index, item):
        """
        Dunderscore method used to insert an item into this list at the specified index

        :type index: int
        :type item: om.MObject
        :rtype: None
        """

        # Check index type
        #
        if not isinstance(index, int):

            raise TypeError('insert() expects an int (%s given)!' % type(index).__name__)

        # Assign item to list
        #
        self.__influences__.insert(index, SkinMixin.pyFactory(item).weakReference())

    def remove(self, value):
        """
        Inherited method used to remove an influence from this instance.

        :type value: Union[int, om.MObject]
        :rtype: None
        """

        # Check value type
        #
        if isinstance(value, int):

            self.__delitem__(value)

        elif isinstance(value, om.MObject):

            self.__delitem__(self.index(value))

        else:

            raise TypeError('Unable to remove null value from list!')

    def index(self, item):
        """
        Dunderscore method used to retrieve the index the supplied item is found at.
        Since we store weak references the respected equal dunderscore methods will not be called...
        If the item can't be found then none will be returned!

        :type item: object
        :rtype: int
        """

        # Iterate through items
        #
        for (influenceId, influence) in self.iterFiltered():

            # Check if items are equivalent
            #
            if influence == item:

                return influenceId

            else:

                continue

        # Return default value
        #
        return None

    @property
    def skinCluster(self):
        """
        Returns the skin cluster associated with this influence list.

        :rtype: SkinMixin
        """

        return self.__skin__()

    def filtered(self):
        """
        Method used to get a dictionary of valid influences from this skin cluster.

        :rtype: dict[int: object]
        """

        return dict(self.iterFiltered())

    def iterFiltered(self):
        """
        Generator method used to iterate through a filter list of influences.
        This list will not contain any null influences!

        :rtype: iter
        """

        # Iterate through influences
        #
        for (influenceId, influence) in self.iteritems():

            # Check for none type
            #
            if influence is not None:

                yield influenceId, influence

            else:

                continue

    def partialPathNames(self):
        """
        Returns a dictionary of valid influence names from this skin cluster.

        :rtype: dict[int:str]
        """

        return {influenceId: influence.partialPathName() for (influenceId, influence) in self.iterFiltered()}

    def fullPathNames(self):
        """
        Returns a dictionary of valid influence names from this skin cluster.

        :rtype: dict[int:str]
        """

        return {influenceId: influence.fullPathName() for (influenceId, influence) in self.iterFiltered()}

    def niceNames(self):
        """
        Property method used to get a dictionary of valid influence names for export.

        :rtype: dict[int:str]
        """

        return {influenceId: influence.displayName() for (influenceId, influence) in self.iterFiltered()}

    def influenceCount(self):
        """
        Method used to determine the number of valid influences from this instance.

        :rtype: int
        """

        return len(self.filtered())

    def influenceIds(self):
        """
        Returns the valid influence IDs.

        :rtype: list[int]
        """

        return self.filtered().keys()

    def nullInfluenceIds(self):
        """
        Returns all of the null influence IDs associated with this instance.

        :rtype: list[int]
        """

        return [influenceId for (influenceId, influence) in self.iteritems() if influence is None]

    def nullInfluenceCount(self):
        """
        Method used to determine how many null influences this instance contains.

        :rtype: int
        """

        return len(self.nullInfluenceIds())

    def nextAvailableSlot(self):
        """
        Method used to locate the first available influence index.

        :rtype: int
        """

        # Iterate through influences
        #
        numInfluences = self.__len__()

        for (influenceId, influence) in self.iteritems():

            # Check for none entry
            #
            if influence is None:

                return influenceId

            else:

                log.debug('Influence ID: %s currently in use...' % influenceId)

        # Return end of list
        #
        return numInfluences

    def selectedPaintInfluence(self):
        """
        Returns the selected influence from the ".paintTrans" attribute on the skin cluster.
        If no connections are found then none will be returned!

        :rtype: int
        """

        # Locate paintTrans plug
        #
        plug = self.skinCluster.findPlug('paintTrans')
        otherPlug = plug.source()

        # Perform index lookup
        #
        return self.index(otherPlug.node())

    def unlockInfluences(self):
        """
        Unlocks all influences attached to this skin cluster.

        :rtype: bool
        """

        # Iterate through influences
        #
        for (influenceId, influence) in self.iterFiltered():

            mc.setAttr('%s.lockInfluenceWeights' % influence.fullPathName(), False)

    def lockInfluences(self):
        """
        Locks all influences attached to this skin cluster.

        :rtype: bool
        """

        # Iterate through influences
        #
        for influenceId, influence in self.iterFiltered():

            mc.setAttr('%s.lockInfluenceWeights' % influence.fullPathName(), True)


class SkinMixin(deformermixin.DeformerMixin):
    """
    Overload of ProxyNode class used to interface with reference nodes.
    Please read the following to under the skin weights vocabulary:
        vertices: Represents a nested dictionary that contain the weights belonging to each vertex.
        vertexIndices: Represents a list of vertex indices that belong to the mesh.
        vertexWeights: Represents a dictionary of influence IDs with their associated weight value.
        falloff: Represents a dictionary of soft selection values correlating to each vertex and its weight.
        influences: Represents a list of influence objects.
        influenceNames: Represents a list of influence names.
        influenceIds: Represents a list of influence IDs associated with the skin cluster.
    """

    __apitype__ = (om.MFn.kSkinClusterFilter, om.MFn.kPluginSkinCluster)

    skinningMethod = mpyattribute.MPyAttribute('skinningMethod')
    normalizeWeights = mpyattribute.MPyAttribute('normalizeWeights')
    maxInfluences = mpyattribute.MPyAttribute('maxInfluences')
    maintainMaxInfluences = mpyattribute.MPyAttribute('maintainMaxInfluences')
    lockWeights = mpyattribute.MPyAttribute('lockWeights')
    dropoffRate = mpyattribute.MPyAttribute('dropoffRate')
    dropoff = mpyattribute.MPyAttribute('dropoff')
    smoothness = mpyattribute.MPyAttribute('smoothness')
    deformUserNormals = mpyattribute.MPyAttribute('deformUserNormals')
    bindPose = mpyattribute.MPyAttribute('bindPose')
    bindVolume = mpyattribute.MPyAttribute('bindVolume')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(SkinMixin, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self._influences = InfluenceObjects(self)
        self._clipboard = {}
        self._colorSetName = 'paintWeightsColorSet1'
        self._colorRamp = '1,0,0,1,1,1,0.5,0,0.8,1,1,1,0,0.6,1,0,1,0,0.4,1,0,0,1,0,1'
        self._defaultRamp = '0,0,0,0,1,0.5,0.5,0.5,0.5,1,1,1,1,1,1'
        self._useColorRamp = False

    def __iter__(self):
        """
        Dunderscore method called whenever a for loop is performed on this instance.

        :rtype: iter
        """

        return self.iterVertices()

    @property
    def pruneTolerance(self):
        """
        Getter method used to prune tolerance for weighted influences.

        :rtype: float
        """

        # Check if variable exists
        #
        if not mc.optionVar(exists='PRUNE_TOLERANCE'):

            mc.optionVar(floatValue=['PRUNE_TOLERANCE', 0.001])

        return mc.optionVar(q='PRUNE_TOLERANCE')

    @pruneTolerance.setter
    def pruneTolerance(self, pruneTolerance):
        """
        Setter method used to update prune tolerance for weighted influences.

        :type pruneTolerance: float
        :rtype: None
        """

        mc.optionVar(floatValue=['PRUNE_TOLERANCE', pruneTolerance])

    @property
    def mirrorTolerance(self):
        """
        Getter method used to access the user threshold setting.
        This value is stored with the Maya user preferences!

        :rtype: float
        """

        # Check if variable exists
        #
        if not mc.optionVar(exists='MIRROR_TOLERANCE'):

            mc.optionVar(floatValue=['MIRROR_TOLERANCE', 0.1])

        return mc.optionVar(q='MIRROR_TOLERANCE')

    @mirrorTolerance.setter
    def mirrorTolerance(self, threshold):
        """
        Setter method used to update the user threshold setting.
        This value is stored within the Maya user preferences!

        :rtype: float
        """

        mc.optionVar(floatValue=['MIRROR_TOLERANCE', threshold])

    @property
    def useColorRamp(self):
        """
        Getter method used to check if skin weights should be colourized.

        :rtype: bool
        """

        return self._useColorRamp

    @useColorRamp.setter
    def useColorRamp(self, useColorRamp):
        """
        Setter method used to edit skin weight colourization behaviour.

        :type useColorRamp: bool
        :rtype: None
        """

        self._useColorRamp = useColorRamp

    @property
    def colorRamp(self):
        """
        Getter method used to get the string based ramp value.
        MPxCommand will be able to parse value using comma delimiter.

        :rtype: str
        """

        return self._colorRamp if self.useColorRamp else self._defaultRamp

    @property
    def clipboard(self):
        """
        Getter method used to retrieve the clipboard.

        :rtype: dict[int:dict[int:float]]
        """

        return self._clipboard

    @property
    def influences(self):
        """
        Returns the influence objects associated with this skin cluster.

        :rtype: InfluenceObjects
        """

        return self._influences

    def iterInfluenceObjects(self):
        """
        Generator method used to iterate through all of the influences associated with this skin cluster.
        Please note there can be gaps in the influence ID sequence.

        :rtype: iter
        """

        # Iterate through matrix elements
        #
        plug = self.findPlug('matrix')
        numElements = plug.evaluateNumElements()

        for i in range(numElements):

            # Get element by index
            #
            element = plug.elementByPhysicalIndex(i)
            index = element.logicalIndex()

            if not element.isConnected:

                log.debug('No connected joint found on %s.matrix[%s]!' % (self.name(), index))
                continue

            # Get connected plug
            #
            otherPlug = element.source()
            otherNode = otherPlug.node()

            if not otherNode.isNull():

                yield index, otherNode

            else:

                log.debug('Null object found on %s.matrix[%s]!' % (self.deformerName(), index))

    @undo
    def addInfluence(self, influence):
        """
        Method used to add a new influence to this skin cluster.

        :type influence: om.MObject
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(influence, om.MObject):

            raise TypeError('addInfluence() expects an MObject (%s given)!' % type(influence).__name__)

        # Check if this is a joint
        #
        if not influence.hasFn(om.MFn.kJoint):

            raise TypeError('addInfluence() expects a joint (%s given)!' % influence.apiTypeStr)

        # Check api type
        #
        fnDagNode = om.MFnDagNode(influence)

        if influence not in self._influences:

            # Get first available index
            #
            index = self._influences.nextAvailableSlot()

            # Connect joint to skin cluster
            #
            fullPathName = fnDagNode.fullPathName()

            mc.connectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (self.name(), index))
            mc.connectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (self.name(), index))

            # Check if ".lockInfluenceWeights" attribute exists
            #
            if not mc.attributeQuery('lockInfluenceWeights', exists=True, node=fullPathName):

                # Add attribute to joint
                # NOTE: These settings were pulled from an ascii file
                #
                mc.addAttr(fullPathName, cachedInternally=True, shortName='liw', longName='lockInfluenceWeights', min=0, max=1, attributeType='bool')

            else:

                log.debug('%s joint already has required attribute.' % fnDagNode.partialPathName())

            # Connect custom attribute
            #
            mc.connectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (self.name(), index))

            # Set pre-bind matrix
            #
            matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % fullPathName)
            mc.setAttr('%s.bindPreMatrix[%s]' % (self.name(), index), matrixList, type='matrix')

            # Add joint to influence list
            #
            self._influences[index] = influence

        else:

            log.warning('Skin cluster already contains influence: %s!' % fnDagNode.partialPathName())
            return

    def addInfluences(self, influences):
        """
        Method used to add a list of influence objects to this skin cluster.

        :type influences: list[om.MObject]
        :rtype: None
        """

        # Iterate through influence objects
        #
        for influence in influences:

            self.addInfluence(influence)

    @undo
    def removeInfluenceId(self, influenceId):
        """
        Method used to remove the influence associated with the given index.

        :type influenceId: int
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(influenceId, int):

            raise TypeError('removeInfluenceId() expects an int (%s given)!' % type(influenceId).__name__)

        # Check if influence ID is defined
        #
        influence = self._influences[influenceId]

        if influence is None:

            log.warning('No influence could be found at ID: %s' % influenceId)
            return

        # Check if influence has any weight assigned to it
        #
        fullPathName = influence.fullPathName()
        usedInfluenceIds = self.getUsedInfluenceIds()

        if influenceId not in usedInfluenceIds:

            # Disconnect joint from skin cluster
            #
            mc.disconnectAttr('%s.worldMatrix[0]' % fullPathName, '%s.matrix[%s]' % (self.name(), influenceId))
            mc.disconnectAttr('%s.objectColorRGB' % fullPathName, '%s.influenceColor[%s]' % (self.name(), influenceId))
            mc.disconnectAttr('%s.lockInfluenceWeights' % fullPathName, '%s.lockWeights[%s]' % (self.name(), influenceId))

            mc.deleteAttr('%s.lockInfluenceWeights' % fullPathName)

            # Remove joint from influence list
            #
            self._influences[influenceId] = None

        else:

            log.warning('%s currently has weight assigned to it!' % influence.partialPathName())
            return

    @undo
    def removeInfluence(self, influence):
        """
        Convenience method used to remove the specified influence ID from the skin cluster.
        This method will also check to see if the influence has any weight assigned to it.

        :type influence: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """

        # Check value type
        #
        influenceId = self._influences.index(influence)

        if influenceId is not None:

            return self.removeInfluenceId(influenceId)

        else:

            log.warning('Unable to locate influence ID...')

    def removeInfluences(self, influences):
        """
        Method used to remove a list of influence objects from this skin cluster.

        :type influences: list[om.MObject]
        :rtype: None
        """

        # Iterate through influence objects
        #
        for influence in influences:

            self.removeInfluence(influence)

    def createInfluenceMap(self, skinCluster, vertexIndices=None):
        """
        Creates an influence map that allows for remapping influence IDs from this instance to the supplied weights.

        :type skinCluster: SkinMixin
        :type vertexIndices: list[int]
        :rtype: dict[int:int]
        """

        # Check skin cluster type
        #
        if not isinstance(skinCluster, SkinMixin):

            raise TypeError('createInfluenceMap() expects SkinMixin (%s given)!' % type(skinCluster).__name__)

        # Iterate through influences
        #
        usedInfluenceIds = self.getUsedInfluenceIds(vertexIndices=vertexIndices)
        influenceMap = {}

        for influenceId in usedInfluenceIds:

            # Try and find a match for the influence name
            #
            influenceName = self._influences[influenceId].partialPathName()
            remappedId = skinCluster.influences.index(influenceName)

            if remappedId is not None:

                influenceMap[influenceId] = remappedId

            else:

                raise KeyError('Unable to find a matching ID for %s influence!' % influenceName)

        # Return influence map
        #
        log.debug('Successfully created %s influence binder.' % influenceMap)
        return influenceMap

    @staticmethod
    def remapVertexWeights(vertices, influenceMap):
        """
        Creates a new vertex weight dictionary based on the supplied influence map.

        :type vertices: dict[int:dict[int:float]]
        :type influenceMap: dict[int:int]
        :rtype: vertices: dict[int:dict[int:float]]
        """

        # Check if arguments are valid
        #
        if not isinstance(vertices, dict) or not isinstance(influenceMap, dict):

            raise TypeError('remapVertexWeights() expects a dict (%s given)!' % type(vertices).__name__)

        # Reiterate through vertices
        #
        updates = {}

        for (vertexIndex, vertexWeights) in vertices.items():

            # Iterate through vertex weights
            #
            updates[vertexIndex] = {}

            for (influenceId, weight) in vertexWeights.items():

                # Get remapped id and check if weights should be merged
                #
                newInfluenceId = influenceMap[influenceId]
                log.debug('Influence ID: %s, has been remapped to: %s' % (influenceId, newInfluenceId))

                if newInfluenceId in updates[vertexIndex]:

                    updates[vertexIndex][newInfluenceId] += weight

                else:

                    updates[vertexIndex][newInfluenceId] = weight

        return updates

    def isPartiallySelected(self):
        """
        Method used to determine if any of the deformer components are selected.
        This includes transform, shape or deformer.

        :rtype: bool
        """

        return self.isSelected() or self.transform().isSelected() or self.shape().isSelected()

    def selection(self):
        """
        Returns the active vertex selection.
        Please note this method will automatically convert any component selection to vertices!

        :rtype: list[int]
        """

        return self.shape().getSelectedVertices().elements()

    def setSelection(self, vertexIndices):
        """
        Updates the active selection for the shape component.

        :type vertexIndices: list[int]
        :rtype: None
        """

        self.shape().selectVertices(vertexIndices)

    def mirrorSelection(self):
        """
        Method used to mirror the active vertex selection.
        Please note this method will not update the active selection!

        :rtype: dict[int:int]
        """

        self.intermediateObject().mirrorVertexIndices(self.selection())

    def softSelection(self):
        """
        Returns the soft selection weights.
        If soft selection is not enabled then an empty dictionary will be returned!

        :rtype: dict[int:float]
        """
        return self.shape().getSelectedVertices().weights()

    def getSkeletonRoot(self):
        """
        Returns the skeleton root associated with this skin cluster.
        If the skin cluster contains multiple roots then a type error will be raised!

        :rtype: mpynode.nodetypes.jointmixin.JointMixin
        """

        # Get all influences
        #
        fullPathNames = list(self._influences.fullPathNames().values())
        commonPrefix = os.path.commonprefix(fullPathNames)

        if commonPrefix is None:

            raise TypeError('Influence objects do not share a common root!')

        # Split pipes
        #
        strings = [x for x in commonPrefix.split('|') if len(x) > 0]
        numStrings = len(strings)

        joint = self.pyFactory.getNodeByName(commonPrefix)

        # Check number of strings
        #
        if numStrings == 0:

            return joint

        # Walk up hierarchy until we find the root joint
        #
        while True:

            # Check if this joint has a parent
            #
            if joint.parentCount() == 0:

                return joint

            # Check if parent is still a joint
            #
            parent = joint.parent()

            if not parent.hasFn(om.MFn.kJoint):

                return joint

            else:

                joint = parent

    @undo
    def resetBindPreMatrices(self):
        """
        Method used to reset the influence objects ".bindPreMatrix" attribute.
        This attribute controls the pose the mesh was bound at on creation.

        :rtype: None
        """

        # Iterate through matrix elements
        #
        plug = self.findPlug('bindPreMatrix')
        numElements = plug.evaluateNumElements()

        for i in range(numElements):

            # Get inverse matrix of influence
            #
            element = plug.elementByPhysicalIndex(i)
            index = element.logicalIndex()

            attributeName = element.name()

            # Check if influence still exists
            #
            influence = self._influences[index]

            if influence is None:

                continue

            # Get inverse matrix from influence-
            #
            matrixList = mc.getAttr('%s.worldInverseMatrix[0]' % influence.fullPathName())
            mc.setAttr(attributeName, matrixList, type='matrix')

        # Prompt user
        #
        log.info('Successfully reset pre-bind matrices on %s!' % self.name())

    @undo
    def resetIntermediateObject(self):
        """
        Bakes the active pose into the intermediate shape.
        This method will also call the "resetBindPreMatrices" function.

        :rtype: None
        """

        # Store deformed points
        #
        iterVertex = om.MItMeshVertex(self.shape().dagPath())
        points = []

        while not iterVertex.isDone():

            point = iterVertex.position()
            points.append([point.x, point.y, point.z])

            iterVertex.next()

        # Reset influences
        #
        self.resetBindPreMatrices()

        # Apply deformed values to intermediate
        #
        iterVertex = om.MItMeshVertex(self.intermediateObject().dagPath())

        while not iterVertex.isDone():

            point = points[iterVertex.index()]
            iterVertex.setPosition(om.MPoint(point))

            iterVertex.next()

    def enableVertexColors(self):
        """
        Edits the shape properties to visualize paint weight colors.

        :rtype: None
        """

        # Check if this instance supports vertex colours
        #
        shape = self.shape()

        if not shape.hasFn(om.MFn.kMesh):

            log.debug('enableVertexColors() expects a mesh (%s given)!' % shape.apiTypeStr)
            return

        # Check if intermediate object has colour set
        #
        intermediateObject = self.intermediateObject()
        colorSetNames = intermediateObject.getColorSetNames()

        if self._colorSetName not in colorSetNames:

            intermediateObject.createColorSet(self._colorSetName, False)
            intermediateObject.setCurrentColorSetName(self._colorSetName)

        # Set shape attributes
        #
        fullPathName = shape.fullPathName()

        mc.setAttr('%s.displayImmediate' % fullPathName, 0)
        mc.setAttr('%s.displayVertices' % fullPathName, 0)
        mc.setAttr('%s.displayEdges' % fullPathName, 0)
        mc.setAttr('%s.displayBorders' % fullPathName, 0)
        mc.setAttr('%s.displayCenter' % fullPathName, 0)
        mc.setAttr('%s.displayTriangles' % fullPathName, 0)
        mc.setAttr('%s.displayUVs' % fullPathName, 0)
        mc.setAttr('%s.displayNonPlanar' % fullPathName, 0)
        mc.setAttr('%s.displayInvisibleFaces' % fullPathName, 0)
        mc.setAttr('%s.displayColors' % fullPathName, 1)
        mc.setAttr('%s.vertexColorSource' % fullPathName, 1)
        mc.setAttr('%s.materialBlend' % fullPathName, 0)
        mc.setAttr('%s.displayNormal' % fullPathName, 0)
        mc.setAttr('%s.displayTangent' % fullPathName, 0)
        mc.setAttr('%s.currentColorSet' % fullPathName, '', type='string')

        # Transfer paint weights
        #
        self.transferPaintWeights()

    def disableVertexColors(self):
        """
        Removes the paint weights color set from the intermediate object.

        :rtype: None
        """

        # Check if this instance supports vertex colours
        #
        shape = self.shape()

        if not shape.hasFn(om.MFn.kMesh):

            log.debug('disableVertexColors() expects a mesh (%s given)!' % shape.apiTypeStr)
            return

        # Reset shape attributes
        #
        fullPathName = shape.fullPathName()

        mc.setAttr('%s.displayColors' % fullPathName, 0)
        mc.setAttr('%s.vertexColorSource' % fullPathName, 1)

        # Delete color set
        #
        intermediateObject = self.intermediateObject()
        colorSetNames = intermediateObject.getColorSetNames()

        if self._colorSetName in colorSetNames:

            intermediateObject.deleteColorSet(self._colorSetName)

    def transferPaintWeights(self):
        """
        Invalidation method used to update vertex colors on the intermediate object.

        :rtype: None
        """

        # Check if this instance belongs to a mesh
        #
        intermediateObject = self.intermediateObject()

        if not intermediateObject.hasFn(om.MFn.kMesh):

            log.debug('transferPaintWeights() expects a mesh (%s given)!' % intermediateObject.apiTypeStr)
            return

        # Check if poly modifier exists
        #
        if intermediateObject.currentColorSetName() == self._colorSetName:

            # Perform paint weight color transfer
            #
            mc.dgdirty('%s.paintTrans' % self.name())

            mc.transferPaintWeights(
                '%s.paintWeights' % self.name(),
                intermediateObject.fullPathName(),
                colorRamp=self._colorRamp
            )

        else:

            log.debug('Unable to transfer paint weights to current colour set!')

    def iterVertices(self, *args, **kwargs):
        """
        Generator method used to iterate through the vertex weights.
        A list of vertices can be supplied to narrow down the yielded values.

        :rtype: iter
        """

        # Check if any arguments were supplied
        #
        vertexIndices = None
        numArgs = len(args)

        if numArgs == 0:

            vertexIndices = range(self.numControlPoints())

        elif numArgs == 1:

            vertexIndices = args[0]

        else:

            raise TypeError('iterVertices() expects at most 1 argument (%s given)!' % numArgs)

        # Iterate through vertices
        #
        for vertexIndex in vertexIndices:

            yield vertexIndex, self.getVertexWeights(vertexIndex)

    def getVertexWeights(self, vertexIndex):
        """
        Method used to collect the influence weights associated with the specified vertex.

        :type vertexIndex: int
        :rtype: dict[int: float]
        """

        # Check value type
        #
        if not isinstance(vertexIndex, int):

            raise TypeError('Unable to get vertex weights using "%s" type!' % type(vertexIndex).__name__)

        # Get plug associated with vertex
        #
        plug = self.findPlug('weightList')
        element = plug.elementByLogicalIndex(vertexIndex)

        child = element.child(0)
        influenceIds = child.getExistingArrayAttributeIndices()

        # Iterate through child array attributes
        #
        vertexWeights = {}

        for influenceId in influenceIds:

            # Check if this is a null influence
            #
            influence = self._influences[influenceId]

            if influence is None:

                # Remove plug element
                #
                log.info(
                    'Removing null influence ID: {influenceId}, from {shape}.vtx[{vertexIndex}]'.format(
                        influenceId=influenceId,
                        shape=self.shape().partialPathName(),
                        vertexIndex=vertexIndex
                    )
                )

                mc.removeMultiInstance(
                    '{name}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                        name=self.name(),
                        vertexIndex=vertexIndex,
                        influenceId=influenceId
                    )
                )

                continue

            # Switch plug element to influence id
            #
            child.selectAncestorLogicalIndex(influenceId, child.attribute())
            vertexWeights[influenceId] = child.asDouble()

        return vertexWeights

    def getVertexWeightsSum(self, vertexWeights, influenceIds=None):
        """
        Convenience method used to get the total sum of the supplied vertex weights.
        An additional list of influence IDs can be supplied to limit the sum to that specific subset.

        :type vertexWeights: dict
        :type influenceIds: list[int]
        :rtype: float
        """

        # Validate arguments
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('getVertexWeightsSum() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check source list before iterating through weights
        #
        if influenceIds is None:

            influenceIds = vertexWeights.keys()

        # Collect weights
        #
        weightValues = []

        for (influenceId, weight) in vertexWeights.items():

            # Check if influence is in source list
            #
            if influenceId in influenceIds:

                weightValues.append(weight)

            else:

                log.debug('Skipping influence ID: %s' % influenceId)

        # Return sum of weights
        #
        return sum(weightValues)

    def getVertices(self, *args, **kwargs):
        """
        Method used to collect vertex weights.
        If no indices are supplied then ALL vertex weights will be returned.

        :rtype: dict[int:dict]
        """

        # Check if any arguments were supplied
        #
        vertexIndices = None
        numArgs = len(args)

        if numArgs == 0:

            vertexIndices = range(self.numControlPoints())

        elif numArgs == 1:

            vertexIndices = args[0]

        else:

            raise TypeError('getVertices() expects at most 1 arguments (%s given)!' % numArgs)

        # Collect vertices
        #
        return {vertexIndex: self.getVertexWeights(vertexIndex) for vertexIndex in vertexIndices}

    def getUsedInfluenceIds(self, vertexIndices=None):
        """
        Method used to collect all used influence IDs.
        An additional list of vertex indices can be supplied to limit this operation.

        :type vertexIndices: list[int]
        :rtype: list[int]
        """

        # Check requested vertices
        #
        if vertexIndices is None:

            vertexIndices = range(self.numControlPoints())

        # Iterate through vertices
        #
        usedInfluenceIds = set()

        for (vertexIndex, vertexWeights) in self.iterVertices(vertexIndices):

            usedInfluenceIds.update(vertexWeights.keys())

        return list(usedInfluenceIds)

    def getUsedInfluenceNames(self, vertexIndices=None):
        """
        Method used to collect all used influence names.
        This method relies on the "getUsedInfluenceIds" to function.

        :type vertexIndices: list[int]
        :rtype: list[str]
        """

        return [self._influences[x].fullPathName() for x in self.getUsedInfluenceIds(vertexIndices=vertexIndices)]

    def getVerticesByInfluenceId(self, influenceIds):
        """
        Returns a list of vertex indices associated with the supplied influence ids.

        :type influenceIds: list[int]
        :rtype: list[int]
        """

        # Check argument type
        #
        if not isinstance(influenceIds, (list, tuple)):

            raise TypeError('getVerticesByInfluenceId() expects a list (%s given)!' % type(influenceIds).__name__)

        # Iterate through vertices
        #
        influenceNames = [self._influences[x].partialPathName() for x in influenceIds]
        vertexIndices = []

        for vertexIndex, vertexWeights in self.iterVertices():

            if len([x for x in influenceIds if x in vertexWeights.keys()]):

                vertexIndices.append(vertexIndex)

            else:

                log.debug(
                    '{shapeName}.vtx[{vertexIndex}] does not contain any {influenceNames} influence.'.format(
                        shapeName=self.shape().name(),
                        vertexIndex=vertexIndex,
                        influenceNames=influenceNames
                    )
                )

        return vertexIndices

    def setVertexWeights(self, vertexIndices, target, source, amount, falloff=None):
        """
        Sets the supplied target influence ID to the specified amount while preserving normalization.

        :type vertexIndices: list[int]
        :type target: int
        :type source: list[int]
        :type amount: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        # Inspect vertex indices
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            raise TypeError('setVertexWeights() expects at least 1 vertex (%s given)!' % numVertices)

        # Inspect influence ids
        #
        if not isinstance(target, int) or len(source) == 0:

            raise TypeError('setVertexWeights() expects a valid target and source list!')

        # Check if falloff weights were supplied
        #
        if not isinstance(falloff, dict):

            falloff = {}

        # Iterate through vertices
        #
        updates = {}

        log.debug('Attempting to set influence ID: %s, for %s.vtx%s' % (target, self.shape().partialPathName(), vertexIndices))
        log.debug('Using %s for source influences.' % source)

        for vertexIndex, vertexWeights in self.iterVertices(vertexIndices):

            # Adjust amount based on soft selection falloff
            #
            softAmount = amount * falloff.get(vertexIndex, 1.0)

            # Copy vertex weights to manipulate
            #
            updates[vertexIndex] = deepcopy(vertexWeights)

            influenceIds = updates[vertexIndex].keys()
            numInfluences = len(influenceIds)

            log.debug('%s affecting %s.vtx[%s]' % (influenceIds, self.shape().partialPathName(), vertexIndex))

            # Get total value of available weights
            #
            total = self.getVertexWeightsSum(vertexWeights, influenceIds=source)
            log.debug('%s weights available to redistribute.' % total)

            # Check if influence exists on vertex
            #
            if target in influenceIds or (target not in influenceIds and numInfluences < self.maxInfluences):

                # Determine redistribution method:
                # If amount is less than current then give those weights back to the source list
                # If amount is greater than current then take weights from the source list
                #
                current = vertexWeights.get(target, 0.0)

                if softAmount < current and 0.0 < total:

                    # Redistribute target weight to source influences
                    #
                    diff = current - softAmount

                    for (influenceId, weight) in vertexWeights.items():

                        # Check if influence is from source
                        #
                        if influenceId in source:

                            # Apply percentage of difference to influence
                            #
                            percent = weight / total
                            newWeight = weight + (diff * percent)

                            updates[vertexIndex][influenceId] = newWeight

                            log.debug(
                                'Adjusting {influenceName} influence from {weight} to {newWeight}'.format(
                                    influenceName=self._influences[influenceId].partialPathName(),
                                    weight=weight,
                                    newWeight=newWeight
                                )
                            )

                        else:

                            log.debug(
                                'Skipping exempted {influenceName} influence.'.format(
                                    influenceName=self._influences[influenceId].partialPathName()
                                )
                            )

                    # Set target to amount
                    #
                    updates[vertexIndex][target] = current - diff

                elif softAmount > current and 0.0 < total:

                    # Make sure amount has not exceeded total
                    #
                    diff = softAmount - current

                    if diff >= total:

                        log.debug('Insufficient weights to pull from. Clamping amount to %s' % total)
                        diff = total

                    # Redistribute source weights to target influences
                    #
                    for (influenceId, weight) in vertexWeights.items():

                        # Check if influence is from source
                        #
                        if influenceId in source:

                            # Reduce influence based on percentage of difference
                            #
                            percent = weight / total
                            newWeight = weight - (diff * percent)

                            updates[vertexIndex][influenceId] = newWeight

                            log.debug(
                                'Reducing {influenceName} influence from {weight} to {newWeight}.'.format(
                                    influenceName=self._influences[influenceId].partialPathName(),
                                    weight=weight,
                                    newWeight=newWeight
                                )
                            )

                        else:

                            log.debug(
                                'Skipping exempted {influenceName} influence.'.format(
                                    influenceName=self._influences[influenceId].partialPathName()
                                )
                            )

                    # Set target to accumulated amount
                    #
                    updates[vertexIndex][target] = current + diff

                else:

                    log.debug(
                        'Unable to set {influenceName} to {softAmount} on {shapeName}.vtx[{vertexIndex}]'.format(
                            influenceName=self._influences[target].partialPathName(),
                            softAmount=softAmount,
                            shapeName=self.shape().name(),
                            vertexIndex=vertexIndex
                        )
                    )

            elif target not in influenceIds and numInfluences >= self.maxInfluences:

                # Check if all influences are being replaced
                #
                if isclose(amount, total, atol=1e-06):

                    updates[vertexIndex] = {target: 1.0}

                elif amount == 0.0:

                    log.debug('No weights available to redistribute from %s.vtx[%s]!' % (self.shape().name(), vertexIndex))

                else:

                    log.warning('Cannot exceed max influences on %s.vtx[%s]!' % (self.shape().name(), vertexIndex))

            else:

                raise TypeError('Unable to set vertex weights using supplied arguments!')

        # Return updated vertex weights
        #
        return updates

    def scaleVertexWeights(self, vertexIndices, target, source, percent, falloff=None):
        """
        Gets a percentage of the total weights to redistribute to target influence.

        :type vertexIndices: list
        :type target: int
        :type source: list[int]
        :type percent: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        # Validate arguments
        #
        numVertices = len(vertexIndices)
        numSource = len(source)

        if numVertices > 0 and isinstance(target, int) and numSource > 0 and isinstance(percent, float):

            # Validate falloff values
            #
            if not isinstance(falloff, dict):

                falloff = {}

            # Iterate through vertices
            #
            updates = {}

            for vertexIndex, vertexWeights in self.iterVertices(vertexIndices):

                # Get amount to redistribute by percentage
                #
                current = vertexWeights.get(target, 0.0)
                amount = current + ((current * percent) * falloff.get(vertexIndex, 1.0))

                # Set vertex weight
                #
                log.debug('Changing %s influence from %s to %s.' % (self._influences[target], current, amount))
                update = self.setVertexWeights([vertexIndex], target, source, amount)

                updates.update(update)

            # Return updated vertex weights
            #
            return updates

        else:

            raise TypeError('Unable to scale weights from invalid arguments!')

    def incrementVertexWeights(self, vertexIndices, target, source, increment, falloff=None):
        """
        Gets a percentage of the total weights to redistribute to target influence.

        :type vertexIndices: list[int]
        :type target: int
        :type source: list[int]
        :type increment: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        # Validate arguments
        #
        numVertices = len(vertexIndices)
        numSource = len(source)

        if numVertices > 0 and isinstance(target, int) and numSource > 0 and isinstance(increment, float):

            # Validate falloff values
            #
            if not isinstance(falloff, dict):

                falloff = {}

            # Iterate through vertices
            #
            updates = {}

            for vertexIndex, vertexWeights in self.iterVertices(vertexIndices):

                # Get amount to redistribute
                #
                current = vertexWeights.get(target, 0.0)
                amount = current + (increment * falloff.get(vertexIndex, 1.0))

                # Set vertex weight
                #
                log.debug('Changing %s influence from %s to %s.' % (self._influences[target], current, amount))
                update = self.setVertexWeights([vertexIndex], target, source, amount)

                updates.update(update)

            # Return updated vertex weights
            #
            return updates

        else:

            raise TypeError('Unable to scale weights from invalid arguments!')

    @undo
    def blendVertices(self):
        """
        Averages the selected vertices based on their neighbouring weights.

        :rtype: bool
        """

        # Get selected vertices
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected == 0:

            return False

        # Iterate through selected vertices
        #
        log.debug('Getting current skin weights for %s.' % selection)
        updates = {}

        for vertexIndex in selection:

            # Get connected vertices
            #
            vertexComponent = self.shape()([vertexIndex], apiType=om.MFn.kMeshVertComponent)
            connectedVertices = vertexComponent.getConnected()

            log.debug('Averaging vertex weights from %s.' % connectedVertices)

            # Average vertex weights
            #
            averageWeights = self.averageVertices(connectedVertices)
            log.debug('%s averaged from connected vertices.' % averageWeights)

            updates[vertexIndex] = averageWeights

        # Apply averaged result to skin cluster
        #
        return self.applyWeights(updates)

    @undo
    def blendBetweenVertices(self, blendByDistance=False):
        """
        Averages all of the vertices between two selected vertices.

        :type blendByDistance: bool
        :rtype: bool
        """

        # Get selected vertices
        #
        selection = self.selection()
        numSelected = len(selection)

        if not (numSelected > 2):

            log.warning('Insufficient number of vertices selected to blend between!')
            return False

        # Invalidate internal skin weights
        #
        vertexComponent = self.intermediateObject()(selection, apiType=om.MFn.kMeshVertComponent)
        vertexComponent.retraceElements()

        startIndex, endIndex = vertexComponent[0], vertexComponent[-1]

        # Copy start and end weights
        #
        vertices = self.getVertices(selection)

        startWeights = deepcopy(vertices[startIndex])
        endWeights = deepcopy(vertices[endIndex])

        # Get max parameter
        #
        maxParam = 0.0
        param = 0.0

        if blendByDistance:

            maxParam = vertexComponent.length()

        else:

            maxParam = float(vertexComponent.numElements - 1)

        # Iterate through elements
        #
        vertexIndices = vertexComponent.elements()
        points = vertexComponent.points()

        updates = {}

        for i, vertexIndex in enumerate(vertexIndices[1:-1]):

            # Get parameter
            #
            if blendByDistance:

                param += points[i].distanceTo(points[i+1])

            else:

                param = float(i + 1)

            # Weighted average start and end vertices
            #
            percent = param / maxParam
            average = self.averageVertexWeights(startWeights, endWeights, percent=percent)

            updates[vertexIndex] = average

        # Apply result to skin cluster
        #
        return self.applyWeights(updates)

    @undo
    def blendBetweenTwoVertices(self, blendByDistance=False, resetActiveSelection=False):
        """
        Averages all of the vertices between two selected vertices.

        :type blendByDistance: bool
        :type resetActiveSelection: bool
        :rtype: bool
        """

        # Get selected vertices
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected != 2:

            log.warning('blendBetweenTwoVertices() expects 2 vertices (%s given)!' % numSelected)
            return False

        # Get shortest edge path between vertices
        #
        edgeIndices = mc.polySelect(
            self.intermediateObject().fullPathName(),
            query=True,
            shortestEdgePath=[selection[0], selection[1]]
        )

        # Convert edge component to vertex component
        #
        edgeComponent = self.shape()(edgeIndices, apiType=om.MFn.kMeshEdgeComponent)

        vertexComponent = edgeComponent.convert(om.MFn.kMeshVertComponent)
        vertexComponent.retraceElements()

        startIndex, endIndex = vertexComponent[0], vertexComponent[-1]

        # Copy start and end weights
        #
        vertices = self.getVertices(selection)

        startWeights = deepcopy(vertices[startIndex])
        endWeights = deepcopy(vertices[endIndex])

        # Get max parameter
        #
        maxParam = 0.0
        param = 0.0

        if blendByDistance:

            maxParam = vertexComponent.length()

        else:

            maxParam = float(vertexComponent.numElements - 1)

        # Update active selection for debugging
        #
        if resetActiveSelection:

            vertexComponent.select()

        # Iterate through elements
        #
        vertexIndices = vertexComponent.elements()
        points = vertexComponent.points()

        updates = {}

        for i, vertexIndex in enumerate(vertexIndices[1:-1]):

            # Get parameter
            #
            if blendByDistance:

                param += points[i].distanceTo(points[i+1])

            else:

                param = float(i + 1)

            # Weighted average start and end vertices
            #
            percent = param / maxParam
            average = self.averageVertexWeights(startWeights, endWeights, percent=percent)

            updates[vertexIndex] = average

        # Apply result to skin cluster
        #
        return self.applyWeights(updates)

    def averageVertexWeights(self, startWeights, endWeights, percent=0.5):
        """
        Averages supplied vertex weights based on a percentage.
        :type startWeights: dict
        :type endWeights: dict
        :param percent: Normalized percentage value to blend between.
        :type percent: float
        :rtype: dict
        """

        # Check vertex weights type
        #
        if not isinstance(startWeights, dict) or not isinstance(endWeights, dict):

            raise TypeError('Cannot average supplied weight values!')

        # Check percentage type
        #
        if not isinstance(percent, (int, float)):

            raise TypeError('Cannot average supplied vertex weights using percentage value!')

        # Merge dictionary keys using null values
        #
        vertexWeights = self.mergeDictionaries([startWeights, endWeights])
        influenceIds = vertexWeights.keys()

        for influenceId in influenceIds:

            # Get weight values
            #
            startWeight = startWeights.get(influenceId, 0.0)
            endWeight = endWeights.get(influenceId, 0.0)

            # Average weights
            #
            averageWeight = (startWeight * (1.0 - percent)) + (endWeight * percent)
            vertexWeights[influenceId] = averageWeight

        # Return normalized weights
        #
        log.debug('Average: %s' % vertexWeights)
        return self.normalizeVertexWeights(vertexWeights)

    def weightedAverageVertexWeights(self, vertices, percentages):
        """
        Averages supplied vertex weights based on a list of weighted averages.
        :type vertices: list
        :type percentages: list[float]
        :rtype: dict
        """

        # Check value types
        #
        numVertices = len(vertices)
        numPercentages = len(percentages)

        weightedSum = sum(percentages)

        if numVertices == numPercentages and isclose(weightedSum, 1.0, atol=1e-06):

            # Merge dictionary keys using null values
            #
            vertexWeights = self.mergeDictionaries(vertices)
            influenceIds = vertexWeights.keys()

            # Iterate through influences
            #
            for influenceId in influenceIds:

                # Collect weight values
                #
                weights = [x.get(influenceId, 0.0) for x in vertices]
                weightedAverage = 0.0

                # Zip list and evaluate in parallel
                #
                for weight, percent in zip(weights, percentages):

                    weightedAverage += weight * percent

                # Assign average to updates
                #
                vertexWeights[influenceId] = weightedAverage

            # Return normalized weights
            #
            log.debug('Weighted Average: %s' % vertexWeights)
            return self.normalizeVertexWeights(vertexWeights)

        else:

            raise TypeError('Cannot perform weighted average from supplied values!')

    def inverseDistanceVertexWeights(self, vertices, distances):
        """
        Averages supplied vertex weights based on the inverse distance.

        :type vertices: dict[int:dict[int:float]]
        :type distances: list[float]
        :rtype: dict
        """

        # Check value types
        #
        numVertices = len(vertices)
        numDistances = len(distances)

        if numVertices != numDistances:

            raise TypeError('inverseDistanceVertexWeights() expects identical length lists!')

        # Check for zero distance
        #
        index = distances.index(0.0) if 0.0 in distances else None

        if index is not None:

            log.debug('Zero distance found in %s' % distances)
            return vertices[index]

        # Merge dictionary keys using null values
        #
        vertexWeights = self.mergeDictionaries(vertices.values())
        influenceIds = vertexWeights.keys()

        # Iterate through influences
        #
        for influenceId in influenceIds:

            # Collect weight values
            #
            weights = [vertexWeights.get(influenceId, 0.0) for vertexWeights in vertices.values()]

            # Zip list and evaluate in parallel
            #
            numerator = 0.0
            denominator = 0.0

            for weight, distance in zip(weights, distances):

                numerator += weight / pow(distance, 2.0)
                denominator += 1.0 / pow(distance, 2.0)

            # Assign average to updates
            #
            vertexWeights[influenceId] = float(numerator / denominator)

        # Return normalized weights
        #
        log.debug('Inverse Distance: %s' % vertexWeights)
        return vertexWeights

    def barycentricAverageVertexWeights(self, polygonIndex, point):
        """
        Performs a barycentric average based on the supplied polygon index and point on that triangle.

        :type polygonIndex: int
        :type point: list[float, float, float]
        :rtype: dict
        """

        # Check if there are enough points
        #
        intermediateObject = self.intermediateObject()
        numPoints = intermediateObject.polygonVertexCount(polygonIndex)

        if numPoints != 3:

            raise TypeError('barycentricAverageVertexWeights() expects 3 points (%s given)!' % numPoints)

        # Define triangle vectors
        #
        vertexIndices = intermediateObject.getPolygonVertices(polygonIndex)
        vectors = om.MVectorArray([intermediateObject.getPoint(x) for x in vertexIndices])

        p0 = vectors[0]
        p1 = vectors[1]
        p2 = vectors[2]
        p3 = om.MVector(point)

        v0 = p1 - p0
        v1 = p2 - p0
        v2 = p3 - p0

        # Get barycentric variables
        #
        d00 = v0 * v0
        d01 = v0 * v1
        d11 = v1 * v1
        d20 = v2 * v0
        d21 = v2 * v1

        invDenom = 0.0

        try:

            invDenom = 1.0 / (d00 * d11 - d01 * d01)

        except ZeroDivisionError:

            log.warning('Divide by zero detected!')

        # Calculate uvw values
        #
        u = (d11 * d20 - d01 * d21) * invDenom
        v = (d00 * d21 - d01 * d20) * invDenom
        w = 1.0 - u - v

        log.debug('U: %s, V: %s, W: %s' % (u, v, w))

        # Return uvw values
        #
        vertices = [self.getVertices([x]).values()[0] for x in vertexIndices]
        vertexWeights = self.weightedAverageVertexWeights(vertices, [w, u, v])

        return vertexWeights

    def bilinearAverageVertexWeights(self, polygonIndex, point):
        """
        See the following for details:
        https://math.stackexchange.com/questions/13404/mapping-irregular-quadrilateral-to-a-rectangle

        :type polygonIndex: int
        :type point: list[float, float, float]
        :rtype: dict
        """

        # Check if there are enough points
        #
        intermediateObject = self.intermediateObject()
        numPoints = intermediateObject.polygonVertexCount(polygonIndex)

        if numPoints != 4:

            raise TypeError('bilinearAverageVertexWeights() expects 4 points (%s given)!' % numPoints)

        # Get vertex weights from polygons
        #
        vertexIndices = intermediateObject.getPolygonVertices(polygonIndex)
        vertices = self.getVertices(vertexIndices)

        # Re-initialize points as vectors
        #
        points = [intermediateObject.getPoint(x) for x in vertexIndices]

        p0 = om.MVector(points[0])
        p1 = om.MVector(points[1])
        p2 = om.MVector(points[2])
        p3 = om.MVector(points[3])

        p = om.MVector(point)

        # Get tangent vectors
        #
        n = intermediateObject.getPolygonNormal(polygonIndex)

        n0 = ((p3 - p0) ^ n).normal()
        n1 = (n ^ (p1 - p0)).normal()
        n2 = (n ^ (p2 - p1)).normal()
        n3 = ((p2 - p3) ^ n).normal()

        # Calculate UV values
        #
        u = ((p - p0) * n0) / (((p - p0) * n0) + ((p - p2) * n2))
        v = ((p - p0) * n1) / (((p - p0) * n1) + ((p - p3) * n3))

        # Average vertex weights
        #
        w0 = self.averageVertexWeights(vertices[vertexIndices[0]], vertices[vertexIndices[1]], percent=u)
        w1 = self.averageVertexWeights(vertices[vertexIndices[3]], vertices[vertexIndices[2]], percent=u)

        vertexWeights = self.averageVertexWeights(w0, w1, percent=v)

        return vertexWeights

    def averageVertices(self, vertexIndices, pruneInfluences=True, useClipboard=False):
        """
        Averages the supplied vertex indices.

        :type vertexIndices: list[int]
        :type pruneInfluences: bool
        :type useClipboard: bool
        :rtype: dict
        """

        # Check vertex count
        #
        numVertices = len(vertexIndices)
        numClipboard = len(self._clipboard)

        if numVertices > 0 or (useClipboard and numClipboard > 0):

            # Check where to pull vertex weights from
            #
            if useClipboard:

                vertices = deepcopy(self._clipboard)

            else:

                vertices = self.getVertices(vertexIndices)

            # Iterate through vertices
            #
            average = {}

            for (vertexIndex, vertexWeights) in vertices.items():

                # Iterate through copied weights
                #
                for (influenceId, vertexWeight) in vertexWeights.items():

                    # Check if influence key already exists
                    #
                    if influenceId not in average:

                        average[influenceId] = vertexWeights[influenceId]

                    else:

                        average[influenceId] += vertexWeights[influenceId]

            # Return normalized result
            #
            return self.normalizeVertexWeights(average, pruneInfluences=pruneInfluences)

        else:

            raise TypeError('averageVertices() expects at least 1 vertex (%s given)!' % numVertices)

    def averageClipboard(self):
        """
        Convenience function for quickly average clipboard weights.

        :rtype: dict
        """

        return self.averageVertices(self._clipboard.keys(), useClipboard=True)

    @classmethod
    def mergeDictionaries(cls, value):
        """
        Combines two dictionaries together with null values.

        :type value: list[dict]
        :rtype: dict
        """

        # Check value type
        #
        if isinstance(value, list):

            # Collect value items
            #
            items = [x for x in value if isinstance(x, dict)]
            keys = set()

            for item in items:

                keys = keys.union(set(item.keys()))

            # Return merged result
            #
            return {key: 0.0 for key in keys}

        elif isinstance(value, (KeysView, ValuesView)):

            return cls.mergeDictionaries(list(value))

        else:

            raise TypeError('mergeDictionaries() expects a list (%s given)!' % type(value).__name__)

    def removeChildWeights(self, parents, vertexIndices=None):
        """
        Method used to redistribute all of child weights to the supplied parent.

        :type parents: list[om.MObject]
        :type vertexIndices: list[int]
        :rtype: None
        """

        # Check if any vertices were supplied
        #
        if vertexIndices is None:

            vertexIndices = range(self.numControlPoints())

        # Get vertex weights from indices
        #
        parents = [self(x) for x in parents]

        parentMap = {self._influences[x]: self._influences[x.descendants(maxDepth=parents)] for x in parents}
        updates = dict.fromkeys(vertexIndices)

        for vertexIndex, vertexWeights in self.iterVertices(vertexIndices):

            # Iterate through each parent id
            #
            updates[vertexIndex] = deepcopy(vertexWeights)

            for (parentId, childIds) in parentMap.items():

                # Iterate through influence ids
                #
                accumulated = 0.0

                for (influenceId, weight) in vertexWeights.items():

                    # Check if this is a child id
                    #
                    if influenceId in childIds:

                        updates[vertexIndex][influenceId] = 0.0
                        accumulated += weight

                # Check if any weights were accumulated
                #
                if accumulated > 0.0:

                    updates[vertexIndex][parentId] = vertexWeights.get(parentId, 0.0) + accumulated

        return self.applyWeights(updates)

    def pruneInfluences(self, vertexWeights):
        """
        Sets all lowest values outside of max influence range to zero.

        :type vertexWeights: dict[int:float]
        :rtype: dict[int:float]
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('pruneInfluences() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check if any influences have dropped below limit
        #
        for (influenceId, weight) in vertexWeights.items():

            # Check if influence weight is below threshold
            #
            influence = self._influences[influenceId]

            if weight < self.pruneTolerance or influence is None:

                vertexWeights[influenceId] = 0.0

            else:

                log.debug('Skipping %s influence.' % influence.partialPathName())

        # Check if influences have exceeded max allowances
        #
        influenceIds = vertexWeights.keys()
        numInfluences = len(influenceIds)

        maxInfluences = self.maxInfluences

        if numInfluences > maxInfluences:

            # Order influences from lowest to highest
            #
            orderedInfluences = sorted(vertexWeights, key=vertexWeights.get, reverse=False)

            # Replace surplus influences with zero values
            #
            diff = numInfluences - maxInfluences

            for i in range(diff):

                influenceId = orderedInfluences[i]
                vertexWeights[influenceId] = 0.0

        else:

            log.debug('Vertex weights have not exceeded max influences.')

        # Return dictionary changes
        #
        return vertexWeights

    def normalizeVertexWeights(self, vertexWeights, pruneInfluences=True):
        """
        Normalizes the supplied weight dictionary.

        :type vertexWeights: dict[int:float]
        :type pruneInfluences: bool
        :rtype: dict.
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('normalizeVertexWeights() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check if influences should be pruned
        #
        if pruneInfluences:

            vertexWeights = self.pruneInfluences(vertexWeights)

        # Check if weights have already been normalized
        #
        isNormalized = self.isNormalized(vertexWeights)

        if isNormalized:

            log.debug('Vertex weights have already been normalized.')
            return vertexWeights

        # Get total weight we can normalize
        #
        total = self.getVertexWeightsSum(vertexWeights)

        if total == 0.0:

            raise TypeError('Cannot normalize influences from zero weights!')

        elif 0.0 < total < 1.0 or total > 1.0:

            # Calculate adjusted scale factor
            #
            scale = 1.0 / total

            for (influenceId, weight) in vertexWeights.items():

                normalized = (weight * scale)
                vertexWeights[influenceId] = normalized

                log.debug(
                    'Scaling {influenceName} influence down from {weight} to {normalized}.'.format(
                        influenceName=self._influences[influenceId].partialPathName(),
                        weight=weight,
                        normalized=normalized
                    )
                )

        else:

            log.debug('Skin weights have already been normalized?')

        # Return normalized vertex weights
        #
        return vertexWeights

    @staticmethod
    def isNormalized(vertexWeights):
        """
        Checks if the supplied weight dictionary has been normalized.

        :type vertexWeights: dict
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('isNormalized() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check influence weight total
        #
        total = sum([weight for (influenceId, weight) in vertexWeights.items()])
        log.debug('Supplied influence weights equal %s.' % total)

        return isclose(1.0, total)

    def copyWeights(self):
        """
        Copies the selected vertices to the clipboard.
        :rtype: None
        """

        # Get active selection
        #
        vertexIndices = self.selection()
        numVertices = len(vertexIndices)

        if numVertices > 0:

            self._clipboard = self.getVertices(vertexIndices)

        else:

            log.debug('Resetting clipboard...')
            self._clipboard = {}

    @undo
    def pasteWeights(self):
        """
        Applies the dictionary stored in the clipboard to the supplied vertices.
        Based on the selection size two different operations can be performed:
            1. If both list are identical then apply the weight list in the same order as the vertices.
            2. Else if neither list is identical then apply the first weight to all of the vertices.

        :rtype: bool
        """

        # Get active selection
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected == 0:

            log.warning('pasteWeights() expect at least 1 selected vertex!')
            return False

        # Check clipboard size
        #
        numClipboard = len(self._clipboard)

        if numClipboard == 0:

            log.warning('pasteWeights() expects at least 1 item from the clipboard!')
            return False

        # Check which operation to perform:
        #
        if numSelected == numClipboard:

            # Reallocate clipboard values to updates
            #
            vertexIndices = zip(self._clipboard.keys(), selection)
            updates = {target: self.getVertexWeights(source) for source, target in vertexIndices}

            return self.applyWeights(updates)

        else:

            # Iterate through vertices
            #
            source = self._clipboard.keys()[-1]
            updates = {vertexIndex: deepcopy(self._clipboard[source]) for vertexIndex in selection}

            return self.applyWeights(updates)

    @undo
    def pasteAveragedWeights(self):
        """
        Averages the vertices stored inside the clipboard and applies them to the active selection.

        :rtype: bool
        """

        # Get active selection
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected == 0:

            log.warning('pasteAveragedWeights() expects at least 1 selected vertex!')
            return False

        # Check clipboard size
        #
        numClipboard = len(self.clipboard)

        if numClipboard > 0:

            # Average all weights in clipboard
            #
            vertexIndices = self.clipboard.keys()

            average = self.averageVertices(vertexIndices, useClipboard=True)
            updates = {vertexIndex: deepcopy(average) for vertexIndex in selection}

            return self.applyWeights(updates)

        else:

            log.warning('pasteAveragedWeights() expects at least 1 item from the clipboard!')
            return False

    @undo
    def slabPasteWeights(self, slabOption=0):
        """
        Copies and pastes the selected vertex weights based on the slab method:
            1: Closest point.
            2: Nearest neighbour.
            3: Along vertex normal.

        :type slabOption: int
        :rtype: bool
        """

        # Get selected vertices
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected == 0:

            log.warning('slabPasteWeights() expects a valid selection!')
            return False

        # Check which method to use
        #
        closest = []
        log.debug('Getting closest vertices for %s.' % selection)

        if slabOption == 0:

            closest = self.intermediateObject().getClosestPoints(selection)

        elif slabOption == 1:

            closest = self.intermediateObject().getNearestNeighbours(selection)

        elif slabOption == 2:

            closest = self.intermediateObject().getVertexAlongNormals(selection)

        else:

            raise TypeError('slabPasteWeights() expects a valid slab option (%s given)!' % slabOption)

        # Check if lists are the same size
        #
        numVertices = len(closest)
        log.debug('Using %s for closest vertices.' % closest)

        if numSelected == numVertices:

            # Get vertex weights
            #
            vertexIndices = set(selection + closest)
            log.debug('Getting weights for %s.' % vertexIndices)

            vertices = self.getVertices(vertexIndices)

            # Compose new weights dictionary
            #
            updates = {target: deepcopy(vertices[source]) for source, target in zip(selection, closest)}
            return self.applyWeights(updates)

        else:

            log.warning('Unable to slab paste selection!')
            return False

    @undo
    def mirrorVertices(self, vertexIndices, pull=False, resetActiveSelection=False):
        """
        Mirrors the supplied vertices to the nearest vertex.

        :type vertexIndices: list[int]
        :type pull: bool
        :type resetActiveSelection: bool
        :rtype: bool
        """

        # Check supplied vertex quantity
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            log.warning('mirrorVertices() expects at least 1 selected vertex!')
            return

        # Get mirrored vertex indices
        #
        mirroredIndices = self.intermediateObject().mirrorVertexIndices(vertexIndices, mirrorTolerance=self.mirrorTolerance)
        updates = {}

        for (vertexIndex, mirrorIndex) in mirroredIndices.items():

            # Get vertex weights associated with indices and reassign
            #
            vertices = self.getVertices([vertexIndex, mirrorIndex])
            isCenterSeam = vertexIndex == mirrorIndex

            if pull:

                # Pull weights from mirror vertex and apply to selection
                #
                vertexWeights = deepcopy(vertices[mirrorIndex])
                mirrorWeights = self.mirrorVertexWeights(vertexWeights, isCenterSeam=isCenterSeam)

                updates[vertexIndex] = mirrorWeights

            else:

                # Get weights from selection and apply to mirror vertex
                #
                vertexWeights = deepcopy(vertices[vertexIndex])
                mirrorWeights = self.mirrorVertexWeights(vertexWeights, isCenterSeam=isCenterSeam)

                updates[mirrorIndex] = mirrorWeights

        # Check if active selection should be reset
        #
        if resetActiveSelection:

            self.shape().selectVertices(updates.keys())

        # Update skin weights
        #
        return self.applyWeights(updates)

    def mirrorVertexWeights(self, vertexWeights, isCenterSeam=False):
        """
        Mirrors the influence IDs in the supplied vertex weight dictionary.

        :type vertexWeights: dict[int: float]
        :type isCenterSeam: bool
        :rtype: dict[int: float]
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('mirrorVertexWeights() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Iterate through influences
        #
        updates = {}

        for influenceId in vertexWeights.keys():

            # Concatenate mirror name
            #
            influenceName = self._influences[influenceId].partialPathName()
            mirrorName = namingutils.mirrorName(influenceName)

            if influenceName is not mirrorName:

                # Check if mirror name is in list
                #
                log.debug('Checking if %s exists in influence list...' % mirrorName)

                if mirrorName in self._influences:

                    # Check if this is for a center seam
                    #
                    if isCenterSeam:

                        log.debug('Splitting %s vertex weights with %s influence.' % (mirrorName, influenceName))

                        mirrorInfluenceId = self._influences[mirrorName]
                        weight = (vertexWeights.get(influenceId, 0.0) + vertexWeights.get(mirrorInfluenceId, 0.0)) / 2.0

                        updates[influenceId] = weight
                        updates[mirrorInfluenceId] = weight

                    else:

                        log.debug('Trading %s vertex weights for %s influence.' % (mirrorName, influenceName))

                        mirrorInfluenceId = self._influences[mirrorName]
                        updates[mirrorInfluenceId] = vertexWeights[influenceId]

                else:

                    log.warning('Unable to find a matching mirrored influence for %s.' % influenceName)
                    updates[influenceId] = vertexWeights[influenceId]

            else:

                log.debug('No mirrored influence name found for %s.' % influenceName)
                updates[influenceId] = vertexWeights[influenceId]

        # Return mirrored vertex weights
        #
        return updates

    @undo
    def applyWeights(self, vertices):
        """
        Updates the skin cluster's weights based on the supplied dictionary.

        :type vertices: dict[int:dict[int:float]]
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(vertices, dict):

            raise TypeError('applyWeights() expects a dict (%s given)!' % type(vertices).__name__)

        # Disable normalize weights
        #
        self.normalizeWeights = False

        # Iterate through vertices
        #
        vertexIndices = vertices.keys()
        current = self.getVertices(vertexIndices)

        for (vertexIndex, vertexWeights) in vertices.items():

            # Diff dictionaries to isolate influences that need pruning
            #
            vertexWeights = self.normalizeVertexWeights(vertexWeights)
            diff = list(set(current[vertexIndex]) - set(vertexWeights))

            for influenceId in diff:

                # Remove array elements from skin cluster
                #
                log.debug(
                    'Removing {influenceName} influence from {shapeName}.vtx[{vertexIndex}]'.format(
                        influenceName=self._influences[influenceId].partialPathName(),
                        shapeName=self.shape().name(),
                        vertexIndex=vertexIndex
                    )
                )

                mc.removeMultiInstance(
                    '{deformerName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                        deformerName=self.name(),
                        vertexIndex=vertexIndex,
                        influenceId=influenceId
                    )
                )

                vertexWeights.pop(influenceId, None)

            # Iterate through influence weights
            #
            updates = deepcopy(vertexWeights)

            for (influenceId, weight) in vertexWeights.items():

                # Check for zero weights
                #
                if isclose(0.0, weight, atol=1e-06):

                    # Remove array elements from skin cluster
                    #
                    log.debug(
                        'Removing {influenceName} influence from {shapeName}.vtx[{vertexIndex}]'.format(
                            influenceName=self._influences[influenceId].partialPathName(),
                            shapeName=self.shape().name(),
                            vertexIndex=vertexIndex
                        )
                    )

                    mc.removeMultiInstance(
                        '{deformerName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                            deformerName=self.name(),
                            vertexIndex=vertexIndex,
                            influenceId=influenceId
                        )
                    )

                    updates.pop(influenceId, None)

                else:

                    # Set array element to new value
                    #
                    log.debug(
                        'Setting {deformerName}.weightList[{vertexIndex}].weights[{influenceId}] to {weight}'.format(
                            deformerName=self.name(),
                            vertexIndex=vertexIndex,
                            influenceId=influenceId,
                            weight=weight
                        )
                    )

                    mc.setAttr(
                        '{deformerName}.weightList[{vertexIndex}].weights[{influenceId}]'.format(
                            deformerName=self.name(),
                            vertexIndex=vertexIndex,
                            influenceId=influenceId
                        ),
                        weight
                    )

        # Re-enable normalize weights and update paint weights
        #
        self.normalizeWeights = True
        self.transferPaintWeights()

    def transferSkinCluster(self, otherMesh, influenceNames=None):
        """
        Convenience method used to copy this skin clusters' influence to another mesh.
        Only used influences can be specified for optimization but will require remapping.

        :type otherMesh: mpynode.nodetypes.meshmixin.MeshMixin
        :type influenceNames: list[str]
        :rtype: SkinMixin
        """

        # Get influence names
        #
        if influenceNames is None:

            influenceNames = self.getUsedInfluenceNames()

        # Create skin cluster
        #
        deformerName = mc.skinCluster(
            influenceNames,
            otherMesh.fullPathName(),
            bindMethod=0,
            skinMethod=self.skinningMethod,
            maximumInfluences=self.maxInfluences,
            obeyMaxInfluences=True,
            toSelectedBones=True,
            normalizeWeights=1
        )[0]

        log.info('Successfully created %s deformer.' % deformerName)
        mc.select(clear=True)

        return self(deformerName)
