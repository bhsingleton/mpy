import sys

from maya import cmds as mc
from maya.api import OpenMaya as om
from collections import deque
from six import string_types
from six.moves import collections_abc
from dcc.maya.libs import dagutils
from . import shapemixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MeshComponent(collections_abc.MutableSequence):
    """
    Overload of `MutableSequence` used to manipulate single indexed components.
    For performance reasons this class will initialize with a fixed dictionary size.
    Any values appended on will update index keys with a positive boolean for faster lookup speeds.
    Please be aware that mesh iterators cannot be created outside the scope of the function they are operating within!
    Once an iterator exits a function it is immediately deleted by the garbage collector.
    """

    # region Dunderscores
    __slots__ = (
        '_handle',
        '_apiType',
        '_apiTypeStr',
        '_weights',
        '_elements',
        '_maxElements',
        '_occupied'
    )

    __iterators__ = {
        om.MFn.kMeshVertComponent: om.MItMeshVertex,
        om.MFn.kMeshEdgeComponent: om.MItMeshEdge,
        om.MFn.kMeshPolygonComponent: om.MItMeshPolygon,
        om.MFn.kMeshVtxFaceComponent: om.MItMeshFaceVertex
    }

    __apiTypeStrs__ = {
        om.MFn.kMeshVertComponent: 'kMeshVertComponent',
        om.MFn.kMeshEdgeComponent: 'kMeshEdgeComponent',
        om.MFn.kMeshPolygonComponent: 'kMeshPolygonComponent',
        om.MFn.kMeshVtxFaceComponent: 'kMeshVtxFaceComponent'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        This class can be instantiated in multiple ways:
        A single value can be supplied containing either a string component or a mesh object.
        Otherwise, a node and component object can be provided if a string argument is not sufficient.
        """

        # Call parent method
        #
        super(MeshComponent, self).__init__()

        # Declare class variables
        #
        self._handle = None
        self._apiType = None
        self._apiTypeStr = None
        self._weights = {}  # This dictionary only exists when initialized via MGlobal.getRichSelection()
        self._elements = deque()
        self._maxElements = None
        self._occupied = None

        # Check number of arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            raise TypeError('%s() expects at least 1 argument (%s given)!' % (self.__class__.__name__, numArgs))

        elif numArgs == 1:

            # Check if this is a string argument
            #
            if isinstance(args[0], string_types):

                # Get component from string
                #
                dagPath, component = dagutils.getComponentFromString(args[0])

                if not component.isNull():

                    self.setHandle(dagPath)
                    self.setComponent(component)

                else:

                    self.setHandle(dagPath)
                    self.setApiType(kwargs.get('apiType', om.MFn.kMeshVertComponent))

            else:

                # Assign empty component
                #
                self.setHandle(args[0])
                self.setApiType(kwargs.get('apiType', om.MFn.kMeshVertComponent))

        elif numArgs == 2:

            # Check component argument type
            #
            self.setHandle(args[0])

            if isinstance(args[1], om.MObject):

                self.setComponent(args[1])

            elif isinstance(args[1], (collections_abc.Sequence, om.MIntArray)):

                self.setApiType(kwargs.get('apiType', om.MFn.kMeshVertComponent))
                self.setElements(args[1])

            else:

                raise TypeError('%s() expects a list (%s given)!' % (self.__class__.__name__, type(args[1]).__name__))

        else:

            raise TypeError('%s() expects at most 2 arguments (%s given)!' % (self.__class__.__name__, numArgs))

    def __add__(self, value):
        """
        Private method called whenever addition is performed on this component.

        :param value: List[int]
        :rtype: MeshComponent
        """

        meshComponent = MeshComponent(self._handle, self._elements, apiType=self._apiType)
        return meshComponent.append(value)

    def __iadd__(self, value):
        """
        Private method called whenever in place addition is performed on this component.

        :type value: List[int]
        :rtype: None
        """

        return self.append(value)

    def __sub__(self, value):
        """
        Private method called whenever subtraction is performed on this component.

        :param value: List[int]
        :rtype: MeshComponent
        """

        meshComponent = MeshComponent(self._handle, self._elements, apiType=self._apiType)
        return meshComponent.remove(value)

    def __isub__(self, value):
        """
        Private method called whenever in place subtraction is performed on this component.

        :type value: List[int]
        :rtype: None
        """

        return self.remove(value)

    def __getitem__(self, key):
        """
        Private method called whenever the user attempts to access an indexed element.

        :type key: int
        :rtype: int
        """

        return self._elements[key]

    def __setitem__(self, key, item):
        """
        Private method called whenever the user attempts to assign an indexed element.
        This method is not supported since it would break the steps taken to optimize this class.

        :type key: int
        :type item: int
        :rtype: None
        """

        pass

    def __delitem__(self, key):
        """
        Private method called whenever the user attempts to delete an indexed element.

        :type key: int
        :rtype: int
        """

        self.remove(key)

    def __contains__(self, value):
        """
        Private method used to check if the component contains the supplied element.

        :type value: int
        :rtype: bool
        """

        # Check value type
        #
        if isinstance(value, int):

            return self._occupied.get(value, False)

        elif isinstance(value, (list, tuple, deque, om.MIntArray)):

            return all([self._occupied.get(x, False) for x in value])

        else:

            raise TypeError('__contains__() expects an int (%s given)!' % type(value).__name__)

    def __iter__(self):
        """
        Returns a generator that yields component indices.

        :rtype: iter
        """

        return iter(self._elements)

    def __len__(self):
        """
        Private method called whenever the len method is used on this component.

        :rtype: int
        """

        return len(self._elements)

    def __call__(self, *args, **kwargs):
        """
        Private method called whenever the user calls this instance.
        A developer can supply elements in order to create a new instance with the same mesh object.

        :rtype: MeshComponent
        """

        return self.__class__(self._handle, *args, apiType=self._apiType)
    # endregion

    # region Properties
    @property
    def apiTypeStr(self):
        """
        Getter method that returns the api type as a human-readable string.

        :rtype: str
        """

        return self._apiTypeStr

    @property
    def numElements(self):
        """
        Getter method that evaluates the number of elements belonging to this component.

        :rtype: int
        """

        return len(self._elements)

    @property
    def maxElements(self):
        """
        Getter method that returns the maximum number of elements this component can have.
        This is dictated by the associated node handle.

        :rtype: int
        """

        return self._maxElements
    # endregion

    # region Methods
    def remove(self, elements):
        """
        Removes the specified elements from this component.

        :type elements: Union[int, List[int], om.MIntArray]
        :rtype: self
        """

        # Check value type
        #
        if isinstance(elements, (collections_abc.Sequence, om.MIntArray)):

            # Iterate through integer items
            #
            for element in elements:

                # Inspect element type
                #
                if not isinstance(element, int):

                    continue

                # Check if element already exists
                #
                if not self._occupied[element]:

                    continue

                # Remove element from queue
                #
                self._occupied[element] = False
                self._elements.remove(element)

            return self

        elif isinstance(elements, int):

            return self.remove([elements])

        else:

            log.warning('Unable to remove elements using "%s" type!' % type(elements).__name__)

    def append(self, elements):
        """
        Appends the supplied elements to this component.

        :type elements: Union[int, List[int], om.MIntArray]
        :rtype: self
        """

        # Check value type
        #
        if isinstance(elements, (collections_abc.Sequence, om.MIntArray)):

            # Iterate through integer items
            #
            for element in elements:

                # Inspect element type
                #
                if not isinstance(element, int):

                    continue

                # Check if element already exists
                #
                if self._occupied[element]:

                    continue

                # Append element from queue
                #
                self._occupied[element] = True
                self._elements.append(element)

            return self

        elif isinstance(elements, int):

            return self.append([elements])

        else:

            raise TypeError('Unable to append elements using "%s" type!' % type(elements).__name__)

    def extend(self, elements):
        """
        Extends this component using the supplied elements.

        :type elements: Union[int, List[int], om.MIntArray]
        :rtype: self
        """

        # Check value type
        #
        if isinstance(elements, (collections_abc.Sequence, om.MIntArray)):

            return self.append(elements)

        elif isinstance(elements, int):

            return self.append([elements])

        else:

            raise TypeError('Unable to extend list using "%s" type!' % type(elements).__name__)

    def insert(self, index, element):
        """
        Inserts an element into this component.

        :type index: int
        :type element: Union[int, List[int], om.MIntArray]
        :rtype: self
        """

        return self.append(element)

    def handle(self):
        """
        Returns the node handle for this instance.

        :rtype: om.MObjectHandle
        """

        return self._handle

    def setHandle(self, value):
        """
        Updates the node handle for this instance.

        :type value: om.MObjectHandle
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, om.MObjectHandle):

            value = dagutils.getMObjectHandle(value)

        self._handle = value

    def node(self):
        """
        Returns the dependency node associated with this component.

        :rtype: om.MObject
        """

        return self._handle.object()

    def dagPath(self):
        """
        Returns a dag path to the associated dependency node.

        :rtype: om.MDagPath
        """

        return om.MDagPath.getAPathTo(self.node())

    def apiType(self):
        """
        Returns the api type associated with this component.

        :rtype: int
        """

        return self._apiType

    def setApiType(self, value):
        """
        Updates the api type associated with this component.
        This will force the max element count to be re-evaluated.

        :type value: int
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, int):

            raise TypeError('setApiType() expect a int (%s given)!' % type(value).__name__)

        # Get max number of elements based on type
        #
        self._apiType = value
        self._apiTypeStr = self.__apiTypeStrs__[self._apiType]

        if self._apiType == om.MFn.kMeshVertComponent:

            self._maxElements = om.MFnMesh(self.dagPath()).numVertices

        elif self._apiType == om.MFn.kMeshPolygonComponent:

            self._maxElements = om.MFnMesh(self.dagPath()).numPolygons

        elif self._apiType == om.MFn.kMeshEdgeComponent:

            self._maxElements = om.MFnMesh(self.dagPath()).numEdges

        elif self._apiType == om.MFn.kMeshVtxFaceComponent:

            self._maxElements = om.MFnMesh(self.dagPath()).numPolygons

        else:

            raise TypeError('setApiType() expect a valid API type (%s given)!' % self._apiType)

    def component(self):
        """
        Returns a component object.

        :return: om.MObject
        """

        return dagutils.createComponent(self.elements(), apiType=self._apiType)

    def setComponent(self, value):
        """
        Updates this component based on the supplied object.

        :type value: om.MObject
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, om.MObject):

            raise TypeError('setComponent() expects an MObject (%s given)!' % type(value).__name__)

        # Check api type
        #
        if value.hasFn(om.MFn.kMeshComponent):

            # Check if component has weights
            #
            fnSingleIndexedComponent = om.MFnSingleIndexedComponent(value)
            numElements = fnSingleIndexedComponent.elementCount

            if fnSingleIndexedComponent.hasWeights:

                # Iterate through component element weights
                #
                log.debug('Iterating through %s component elements.' % numElements)
                self._weights = {}

                for i in range(numElements):

                    # Get influence weight
                    #
                    element = fnSingleIndexedComponent.element(i)
                    weight = fnSingleIndexedComponent.weight(i).influence

                    self._weights[element] = weight

            else:

                self._weights = {fnSingleIndexedComponent.element(x): 1.0 for x in range(numElements)}

            # Get component elements
            #
            self.setApiType(value.apiType())
            self.setElements(fnSingleIndexedComponent.getElements())

        else:

            raise TypeError('setComponent() expects mesh component (%s given)!' % value.apiTypeStr)

    def elements(self):
        """
        Returns the elements associated with this component.

        :rtype: List[int]
        """

        return list(self._elements)

    def setElements(self, value):
        """
        Updates the elements belonging to this component.

        :type value: Union[int, MutableSequence, om.MIntArray]
        :rtype: None
        """

        # Check value type
        #
        if isinstance(value, om.MIntArray):

            # Reset private properties
            #
            self._occupied = dict.fromkeys(range(self._maxElements), False)
            self._elements = deque()

            self.append(value)

        elif isinstance(value, collections_abc.MutableSequence):

            return self.setElements(om.MIntArray(value))

        elif isinstance(value, int):

            return self.setElements(om.MIntArray([value]))

        else:

            raise TypeError('Unable to set elements using %s!' % type(value).__name__)

    def sorted(self):
        """
        Returns a sorted list of elements from this component.

        :rtype: List[int]
        """

        return list(sorted(self._elements))

    def weights(self):
        """
        Returns the soft selection weight values.
        Only component objects returned via getRichSelection will have weights!

        :rtype: dict[int:float]
        """

        return self._weights

    def hasWeights(self):
        """
        Evaluates whether this component has weights.
        Only component objects returned via getRichSelection will have weights!

        :rtype: bool
        """

        return len(self._weights) > 0

    def getConnectedVertices(self, *args):
        """
        Returns a list of connected vertices.
        Since no dag paths can be created for kMeshData types different iteration methods have to be used.

        :rtype: deque
        """

        # Check value type
        #
        elements = None
        numArgs = len(args)

        if numArgs == 0:

            elements = self._elements

        elif numArgs == 1:

            elements = args[0]

        else:

            elements = [x for x in args if isinstance(x, int)]

        # Check which iterator methods to use
        #
        vertexIndices = deque()

        iterator = self.__iterators__[self._apiType].__call__(self.node())
        queue = deque(elements)

        if isinstance(iterator, om.MItMeshVertex):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getConnectedVertices()
                vertexIndices.extend(connected)

        elif isinstance(iterator, om.MItMeshEdge):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = [iterator.vertexId(0), iterator.vertexId(1)]
                vertexIndices.extend(connected)

        elif isinstance(iterator, om.MItMeshPolygon):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getVertices()
                vertexIndices.extend(connected)

        else:

            raise TypeError('getConnectedVertices() expects a valid iterator (%s given)!' % type(iterator).__name__)

        return vertexIndices

    def getConnectedEdges(self, *args):
        """
        Returns a list of connected edges.
        Since no dag paths can be created for kMeshData types different iteration methods have to be used.

        :rtype: deque
        """

        # Check value type
        #
        elements = None
        numArgs = len(args)

        if numArgs == 0:

            elements = self._elements

        elif numArgs == 1:

            elements = args[0]

        else:

            elements = [x for x in args if isinstance(x, int)]

        # Check which iterator methods to use
        #
        edgeIndices = deque()

        iterator = self.__iterators__[self._apiType].__call__(self.node())
        queue = deque(elements)

        if isinstance(iterator, (om.MItMeshVertex, om.MItMeshEdge)):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getConnectedEdges()
                edgeIndices.extend(connected)

        elif isinstance(iterator, om.MItMeshPolygon):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getConnectedEdges()
                edgeIndices.extend(connected)

        else:

            raise TypeError('getConnectedEdges() expects a valid iterator (%s given)!' % type(iterator).__name__)

        return edgeIndices

    def getConnectedFaces(self, *args):
        """
        Returns a list of connected faces.

        :rtype: deque
        """

        # Check value type
        #
        elements = None
        numArgs = len(args)

        if numArgs == 0:

            elements = self._elements

        elif numArgs == 1:

            elements = args[0]

        else:

            elements = [x for x in args if isinstance(x, int)]

        # Check which iterator methods to use
        #
        faceIndices = deque()

        iterator = self.__iterators__[self._apiType].__call__(self.node())
        queue = deque(elements)

        if isinstance(iterator, (om.MItMeshVertex, om.MItMeshEdge)):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getConnectedFaces()
                faceIndices.extend(connected)

        elif isinstance(iterator, om.MItMeshPolygon):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                connected = iterator.getConnectedFaces()
                faceIndices.extend(connected)

        else:

            raise TypeError('getConnectedFaces() expects a valid iterator (%s given)!' % type(iterator).__name__)

        return faceIndices

    def getConnected(self, apiType=None):
        """
        Returns a list of connected components.
        The supplied api type will dictate the behaviour of this function.

        :type apiType: int
        :rtype: deque
        """

        # Check requested api type
        #
        if apiType is None:

            apiType = self._apiType

        # Evaluate requested type
        #
        if apiType == om.MFn.kMeshVertComponent:

            return self.getConnectedVertices(self._elements)

        elif apiType == om.MFn.kMeshEdgeComponent:

            return self.getConnectedEdges(self._elements)

        elif apiType == om.MFn.kMeshPolygonComponent:

            return self.getConnectedFaces(self._elements)

        else:

            raise TypeError('getConnected() expects a valid mesh component type (%s given)!' % apiType)

    def convert(self, apiType):
        """
        Converts this component to the specified api type.

        :type apiType: int
        :rtype: Union[MeshVertexComponent, MeshEdgeComponent, MeshPolygonComponent]
        """

        # Create new component
        #
        elements = self.elements() if apiType == self.apiType() else self.getConnected(apiType=apiType)

        if apiType == om.MFn.kMeshVertComponent:

            return MeshVertexComponent(self.handle(), elements)

        elif apiType == om.MFn.kMeshEdgeComponent:

            return MeshEdgeComponent(self.handle(), elements)

        elif apiType == om.MFn.kMeshPolygonComponent:

            return MeshPolygonComponent(self.handle(), elements)

        else:

            raise TypeError(f'convert() expects a valid mesh component type ({apiType} given)!')

    def grow(self):
        """
        Grows this component by appending the connected components.

        :rtype: self
        """

        # Get connected components
        #
        connected = self.getConnected()
        self.append(connected)

        return self

    def center(self):
        """
        Returns the averaged center of all active elements.
        For simplicity all iterators consume items in order to support mesh data objects.

        :rtype: om.MPoint
        """

        # Check which iterator methods to use
        #
        center = om.MPoint([0.0, 0.0, 0.0, 1.0])
        weight = 1.0 / self.numElements

        iterator = self.__iterators__[self._apiType].__call__(self.dagPath())
        queue = deque(self._elements)

        log.debug('Iterating through %s elements.' % iterator.count())

        if isinstance(iterator, om.MItMeshVertex):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                center += iterator.position() * weight

        elif isinstance(iterator, (om.MItMeshEdge, om.MItMeshPolygon)):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                center += iterator.center() * weight

        else:

            raise TypeError('center() expects a valid iterator (%s given)!' % type(iterator).__name__)

        return center

    def points(self):
        """
        Returns all the points associated with this component.

        :rtype: om.MPointArray
        """

        # Check which iterator methods to use
        #
        points = om.MPointArray()

        iterator = self.__iterators__[self._apiType].__call__(self.dagPath())
        queue = deque(self._elements)

        log.debug('Iterating through %s elements.' % iterator.count())

        if isinstance(iterator, om.MItMeshVertex):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                points.append(iterator.position())

        elif isinstance(iterator, (om.MItMeshEdge, om.MItMeshPolygon)):

            # Consume all elements
            #
            while len(queue):

                index = queue.popleft()
                iterator.setIndex(index)

                points.append(iterator.center())

        else:

            raise TypeError('points() expects a valid iterator (%s given)!' % type(iterator).__name__)

        return points

    def select(self):
        """
        Selects the associated mesh component inside the viewport.

        :rtype: None
        """

        # Define selection list
        #
        selection = om.MSelectionList()
        selection.add(tuple([self.dagPath(), self.component()]))

        om.MGlobal.setActiveSelectionList(selection)

    def getSelectionStrings(self):
        """
        Returns the selection strings used to recreate this component.

        :rtype: List[str]
        """

        # Define selection list
        #
        selection = om.MSelectionList()
        selection.add(tuple([om.MDagPath().getAPathTo(self.dagPath()), self.component]))

        return selection.getSelectionStrings()

    def shell(self):
        """
        Returns the shell of this component.

        :rtype: MeshComponent
        """

        # Check if there are enough component elements to grow from
        #
        if self.numElements > 0:

            # Define new shell component
            #
            shell = self.__class__(self.handle(), self._elements)

            # Get max recursion
            #
            recursionLimit = sys.getrecursionlimit()

            # Check if component can be grown
            #
            connected = shell.getConnected(apiType=self._apiType)
            growthSize = len(connected)

            iterations = 0

            while growthSize > 0 and iterations <= recursionLimit:

                # Check growth size
                #
                diff = shell.difference(connected)
                growthSize = len(diff)

                # Append difference and grow elements again
                #
                shell.append(diff)
                connected = shell.getConnected(apiType=self._apiType)

                iterations += 1

            return shell

        else:

            log.debug('Unable to get shell from empty selection.')
            return self

    def shells(self):
        """
        Returns a list of all the shells belonging to the associated mesh.

        :rtype: List[List[int]]
        """

        # Initialize iterator
        #
        dagPath = om.MDagPath().getAPathTo(self.dagPath())
        iterator = self.__iterators__[self._apiType].__call__(dagPath)

        # Iterate through all components
        #
        queue = deque(range(self._maxElements))
        shells = []

        while len(queue):

            # Check if index exists in shells
            #
            currentIndex = queue.popleft()
            iterator.setIndex(currentIndex)

            if not any([currentIndex in shell for shell in shells]):

                # Get current component and append shell
                #
                currentItem = iterator.currentItem()

                shell = self.__class__(self.dagPath(), currentItem).shell()
                shells.append(shell)

            else:

                log.debug('Skipping %s index...' % currentIndex)

        return shells

    def intersection(self, value):
        """
        Returns a list of items that exist in both lists.

        :type value: List[int]
        :rtype: List[int]
        """

        # Check value type
        #
        if isinstance(value, (collections_abc.Sequence, om.MIntArray)):

            return [x for x in value if self._occupied.get(x, False)]

        else:

            raise TypeError('Unable to intersect lists using "%s" type!' % type(value).__name__)

    def difference(self, value):
        """
        Returns a list of items that are unique to both lists.

        :type value: List[int]
        :rtype: List[int]
        """

        # Check value type
        #
        if isinstance(value, (collections_abc.Sequence, om.MIntArray)):

            return [x for x in value if not self._occupied.get(x, True)]

        else:

            raise TypeError('Unable to intersect lists using "%s" type!' % type(value).__name__)

    @classmethod
    def fromSelection(cls):
        """
        Returns a mesh component from the active selection.

        :rtype: MeshComponent
        """

        # Inspect active selection
        #
        selection = list(dagutils.iterActiveComponentSelection())
        selectionCount = len(selection)

        if selectionCount != 1:

            raise TypeError('fromSelection() expects 1 selected mesh (%s given)!' % selectionCount)

        return cls(*selection[0])
    # endregion


class MeshVertexComponent(MeshComponent):
    """
    Overload of `MeshComponent` that interfaces with mesh vertex components.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(MeshVertexComponent, self).__init__(*args, apiType=om.MFn.kMeshVertComponent)
    # endregion

    # region Methods
    def getColors(self, colorSetName=None, asHexCode=False):
        """
        Returns a list colours associated with this vertex component.
        This method does not accommodate for face-vertex colours.

        :type colorSetName: str
        :type asHexCode: bool
        :rtype: List[str]
        """

        # Consume all elements
        #
        iterator = om.MItMeshVertex(self.dagPath())
        queue = deque(self._elements)

        vertexColors = {}

        while len(queue):

            # Get all colors associated with vertex
            #
            index = queue.popleft()
            iterator.setIndex(index)

            colors = iterator.getColors(colorSetName=colorSetName)

            if asHexCode:

                vertexColors[index] = set('#%02x%02x%02x' % (int(color.r * 255), int(color.g * 255), int(color.b * 255)) for color in colors)

            else:

                vertexColors[index] = set(colors)

        return vertexColors

    def retraceElements(self):
        """
        Reorders the internal elements to maintain a vertex loop.
        A type error will be raised this component is not an edge loop!

        :rtype: None
        """

        # Find the edges that only have one connected edge
        #
        connectionCounts = [len([y for y in self.getConnectedVertices([x]) if self._occupied[y]]) for x in self._elements]
        vertexTips = [self._elements[x] for (x, y) in enumerate(connectionCounts) if y == 1]

        startIndex = vertexTips[0] if len(vertexTips) == 2 else self._elements[0]

        # Re-traverse connected edges
        #
        previousIndex = startIndex
        reordered = [startIndex]

        success = True

        while len(reordered) != self.numElements:

            # Go to next edge
            #
            connectedVertices = [x for x in self.getConnectedVertices([previousIndex]) if x not in reordered and self._occupied[x]]
            numConnectedVertices = len(connectedVertices)

            if numConnectedVertices == 0:

                success = False
                break

            else:

                # Append item to traversed
                #
                previousIndex = connectedVertices[0]
                reordered.append(previousIndex)

        # Reassign elements
        #
        if success:

            self._elements = deque(reordered)

        return success

    def length(self):
        """
        Returns the length of this vertex component.

        :rtype: float
        """

        # Iterate through elements
        #
        fnMesh = om.MFnMesh(self.handle().object())
        distance = 0.0

        for i in range(1, self.numElements, 1):

            point1 = fnMesh.getPoint(self._elements[i-1])
            point2 = fnMesh.getPoint(self._elements[i])

            distance += point1.distanceTo(point2)

        return distance
    # endregion


class MeshEdgeComponent(MeshComponent):
    """
    Overload of `MeshComponent` that interfaces with mesh edge components.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(MeshEdgeComponent, self).__init__(*args, apiType=om.MFn.kMeshEdgeComponent)
    # endregion

    # region Methods
    def retraceElements(self):
        """
        Reorders the internal elements to maintain an edge loop.

        :rtype: bool
        """

        # Find the edge tips
        #
        connectionCounts = [len([y for y in self.getConnectedEdges([x]) if self._occupied[y]]) for x in self._elements]
        edgeTips = [self._elements[x] for (x, y) in enumerate(connectionCounts) if y == 1]

        startIndex = edgeTips[0] if len(edgeTips) == 2 else self._elements[0]

        # Re-traverse connected edges
        #
        previousIndex = startIndex
        reordered = [startIndex]

        success = True

        while len(reordered) != self.numElements:

            # Go to next edge
            #
            connectedEdges = [x for x in self.getConnectedEdges([previousIndex]) if x not in reordered and self._occupied[x]]
            numConnectedEdges = len(connectedEdges)

            if numConnectedEdges == 0:

                success = False
                break

            # Append item to traversal tracker
            #
            previousIndex = connectedEdges[0]
            reordered.append(previousIndex)

        # Reassign elements
        #
        if success:

            self._elements = deque(reordered)

        return success

    def associatedVertices(self, ordered=False):
        """
        Returns a list of vertex elements that make up this edge component.

        :type ordered: bool
        :rtype: List[int]
        """

        # Check if ordered vertices are required
        #
        if ordered:

            # Reorder internal elements
            #
            success = self.retraceElements()

            if not success:

                return []

            # Iterate through elements
            #
            vertexIndices = []
            iterator = self.__iterators__[self.apiType()](self.dagPath())

            for (i, element) in enumerate(self._elements):

                # Check if edge direction requires re-evaluation
                #
                if i == 1:

                    iterator.setIndex(element)
                    startIndex, endIndex = iterator.vertexId(0), iterator.vertexId(1)

                    if vertexIndices[-1] not in (startIndex, endIndex):

                        vertexIndices[0], vertexIndices[1] = vertexIndices[1], vertexIndices[0]

                    vertexIndices.extend([index for index in (startIndex, endIndex) if index not in vertexIndices])

                else:

                    iterator.setIndex(element)
                    startIndex, endIndex = iterator.vertexId(0), iterator.vertexId(1)

                    vertexIndices.extend([index for index in (startIndex, endIndex) if index not in vertexIndices])

            return vertexIndices

        else:

            # Iterate through elements
            #
            vertexIndices = set()
            iterator = self.__iterators__[self.apiType()](self.dagPath())

            for element in self._elements:

                iterator.setIndex(element)
                vertexIndices.add(iterator.vertexId(0))
                vertexIndices.add(iterator.vertexId(1))

            return list(vertexIndices)

    def length(self):
        """
        Returns the length of this edge component.

        :rtype: float
        """

        raise NotImplementedError()
    # endregion


class MeshPolygonComponent(MeshComponent):
    """
    Overload of `MeshComponent` that interfaces with mesh polygon components.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(MeshPolygonComponent, self).__init__(*args, apiType=om.MFn.kMeshPolygonComponent)
    # endregion

    # region Methods
    def getEdges(self, indices=None):
        """
        Method used to collect interior edges rather than connected edges.
        An optional list of indices can be provided to query instead of the internal elements.

        :type indices: List[int]
        :rtype: List[int]
        """

        # Check for supplied indices
        #
        if indices is None:

            indices = self._elements

        # Consume all elements
        #
        iterator = om.MItMeshPolygon(self.dagPath())
        queue = deque(indices)

        edgeIndices = deque()

        while len(queue):

            index = queue.popleft()
            iterator.setIndex(index)

            edgeIndices.extend(iterator.getEdges())

        return list(edgeIndices)

    def getEdgeBoundary(self):
        """
        Converts this component to an edge boundary.

        :rtype: List[int]
        """

        # Collect boundary edges
        #
        edgeComponent = self.convert(om.MFn.kMeshEdgeComponent)
        boundary = deque()

        for edgeIndex in edgeComponent:

            # Get connected faces
            #
            connectedFaces = edgeComponent.getConnectedFaces([edgeIndex])
            numConnectedFaces = len(connectedFaces)

            if numConnectedFaces == 1:  # Redundancy check

                boundary.append(edgeIndex)
                continue

            # Collect faces that are in this component
            #
            containedFaces = [faceIndex for faceIndex in connectedFaces if faceIndex in self]
            numContainedFaces = len(containedFaces)

            if numContainedFaces == 1:

                boundary.append(edgeIndex)

            else:

                continue

        return list(boundary)

    def getVertices(self, indices=None):
        """
        Method used to collect interior vertices rather than connected vertices.
        An optional list of indices can be provided to query instead of the internal elements.

        :type indices: List[int]
        :rtype: List[int]
        """

        # Check for supplied indices
        #
        if indices is None:

            indices = self._elements

        # Iterate through component
        #
        iterator = om.MItMeshPolygon(self.dagPath())
        queue = deque(indices)

        vertexIndices = deque()

        while len(queue):

            index = queue.popleft()
            iterator.setIndex(index)

            vertexIndices.extend(iterator.getVertices())

        return list(vertexIndices)
    # endregion


class MeshMixin(shapemixin.ShapeMixin):
    """
    Overload of `ShapeMixin` that interfaces with mesh nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kMesh

    __components__ = {
        om.MFn.kMeshVertComponent: MeshVertexComponent,
        om.MFn.kMeshEdgeComponent: MeshEdgeComponent,
        om.MFn.kMeshPolygonComponent: MeshPolygonComponent
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(MeshMixin, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """
        Private method called whenever the user evokes this class.
        This method will return a mesh component based on the supplied elements.

        :type args: Union[List[int], om.MObject]
        :key apiType: int
        :rtype: Union[MeshVertexComponent, MeshEdgeComponent, MeshPolygonComponent]
        """

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs != 1:

            raise TypeError(f'__call__() expects 1 argument ({numArgs} given)!')

        # Evaluate argument type
        #
        arg = args[0]

        if isinstance(arg, om.MObject):

            # Evaluate api type
            #
            apiType = arg.apiType()
            componentType = self.__class__.__components__.get(apiType, None)

            if callable(componentType):

                return componentType(self.handle(), arg)

            else:

                raise TypeError(f'__call__() a compatible API type ({apiType} given)!')

        elif isinstance(arg, collections_abc.Sequence):

            # Evaluate api type
            #
            apiType = kwargs.get('apiType', om.MFn.kMeshVertComponent)
            componentType = self.__class__.__components__.get(apiType, None)

            if callable(componentType):

                return componentType(self.handle(), arg)

            else:

                raise TypeError(f'__call__() a compatible API type ({apiType} given)!')

        else:

            raise TypeError(f'__call__() expects either a list or MObject ({type(arg).__name__} given)!')
    # endregion

    # region Methods
    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnMesh
        """

        return super(MeshMixin, self).functionSet()

    def controlPoints(self):
        """
        Returns the control points for this shape.

        :rtype: om.MPointArray
        """

        return self.functionSet().getPoints()

    def setControlPoints(self, controlPoints, space=om.MSpace.kObject):
        """
        Returns the control points for this shape.

        :type controlPoints: om.MPointArray
        :type space: int
        :rtype: None
        """

        functionSet = self.functionSet()  # type: om.MFnMesh
        functionSet.setPoints(controlPoints, space=space)
        functionSet.updateSurface()

    def numControlPoints(self):
        """
        Evaluates the number of control points for this shape.

        :rtype: int
        """

        return self.functionSet().numVertices

    def selectVertices(self, vertexIndices):
        """
        Selects the supplied vertex indices.

        :type vertexIndices: List[int]
        :rtype: none
        """

        MeshVertexComponent(self.handle(), vertexIndices).select()

    def getSelectedVertices(self):
        """
        Returns the selected vertices from this mesh.

        :rtype: MeshVertexComponent
        """

        # Get constructor arguments
        #
        handle = self.handle()
        component = self.component()

        if component.hasFn(om.MFn.kMeshComponent):

            return MeshComponent(handle, component).convert(om.MFn.kMeshVertComponent)

        else:

            return MeshVertexComponent(handle)

    def selectPolygons(self, polygonIndices):
        """
        Selects the supplied polygon indices.

        :type polygonIndices: List[int]
        :rtype: none
        """

        MeshPolygonComponent(self.handle(), polygonIndices).select()

    def getSelectedPolygons(self):
        """
        Returns the selected polygons from this mesh.

        :rtype: MeshPolygonComponent
        """

        # Get constructor arguments
        #
        handle = self.handle()
        component = self.component()

        if component.hasFn(om.MFn.kMeshComponent):

            return MeshComponent(handle, component).convert(om.MFn.kMeshPolygonComponent)

        else:

            return MeshPolygonComponent(handle)

    def selectEdges(self, edgeIndices):
        """
        Selects the supplied edge indices.

        :type edgeIndices: List[int]
        :rtype: none
        """

        MeshEdgeComponent(self.handle(), edgeIndices).select()

    def getSelectedEdges(self):
        """
        Returns the selected edges from this mesh.

        :rtype: MeshEdgeComponent
        """

        # Get constructor arguments
        #
        handle = self.handle()
        component = self.component()

        if component.hasFn(om.MFn.kMeshComponent):

            return MeshComponent(handle, component).convert(om.MFn.kMeshEdgeComponent)

        else:

            return MeshEdgeComponent(handle)

    def selectShell(self):
        """
        Expands the active selection to all the connected component elements.

        :rtype: None
        """

        # Check active component
        #
        component = self.component()

        if component.isNull():

            log.debug('selectShell() expects at least 1 selection component!')
            return

        # Select shell component
        #
        shell = MeshComponent(self.handle(), component).shell()
        shell.select()
    # endregion
