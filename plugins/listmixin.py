from maya.api import OpenMaya as om
from dcc.python import stringutils
from .. import mpyattribute
from ..builtins import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ListMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with list nodes.
    """

    # region Attributes
    active = mpyattribute.MPyAttribute('active')
    average = mpyattribute.MPyAttribute('average')
    # endregion

    # region Dunderscores
    __plugin__ = ('positionList', 'rotationList', 'scaleList')
    # endregion

    # region Methods
    def getAssociatedTransform(self):
        """
        Returns the transform associated with this list node.

        :rtype: transformmixin.TransformMixin
        """

        dependents = self.dependsOn(apiType=om.MFn.kPluginTransformNode, typeName='maxform')
        numDependents = len(dependents)

        if numDependents > 0:

            return dependents[0]

        else:

            log.warning(f'Cannot locate associated transform for: {self}')
            return None

    def numElements(self):
        """
        Evaluates the number of elements in this list.

        :rtype: int
        """

        return self.findPlug('list').numElements()

    def iterElements(self):
        """
        Returns a generator that yields list elements.

        :rtype: Iterator[ListElement]
        """

        numElements = self.numElements()

        for i in range(numElements):

            yield ListElement(self, index=i)

    def insertElement(self, index, name, absolute, weight, value, source=None):
        """
        Inserts a new element into this list.

        :type index: int
        :type name: str
        :type absolute: bool
        :type weight: float
        :type value: Tuple[float, float, float]
        :type source: Union[Tuple[om.MPlug, om.MPlug, om.MPlug], None]
        :rtype: ListElement
        """

        # Make room for new element
        #
        numElements = self.numElements()
        indices = list(range(index, numElements))

        for index in reversed(indices):

            self.moveElement(index, index + 1)

        # Insert new element
        #
        element = ListElement(self, index=index)
        element.setName(name)
        element.setAbsolute(absolute)
        element.setWeight(weight)
        element.setValue(value)
        element.setSource(source)

        return element

    def moveElement(self, oldIndex, newIndex):
        """
        Moves the element at the old index to the new index.

        :type oldIndex: int
        :type newIndex: int
        :rtype: ListElement
        """

        oldElement = ListElement(self, index=oldIndex)

        newElement = ListElement(self, index=newIndex)
        newElement.setName(oldElement.name())
        newElement.setAbsolute(oldElement.absolute())
        newElement.setWeight(oldElement.weight())
        newElement.setValue(oldElement.value())
        newElement.setSource(oldElement.source())

        return newElement
    # endregion


class ListElement(object):
    """
    Base class used to interface with list elements.
    """

    # region Dunderscores
    __slots__ = ('_list', '_index')
    __attributes__ = {'positionList': 'position', 'rotationList': 'rotation', 'scaleList': 'scale'}

    def __init__(self, node, **kwargs):
        """
        Private method called after a new instance has been created.

        :type node: ListMixin
        :rtype: None
        """

        # Call parent method
        #
        super(ListElement, self).__init__()

        # Declare class variables
        #
        self._list = node.weakReference()
        self._index = kwargs.get('index', 0)
    # endregion

    # region Properties
    @property
    def list(self):
        """
        Getter method that returns the associated list node for this element.

        :rtype: AbstractListMixin
        """

        return self._list()

    @property
    def index(self):
        """
        Getter method that returns the index for this list element.

        :rtype: int
        """

        return self._index
    # endregion

    # region Methods
    def isActive(self):
        """
        Evaluates if this list element is currently active.

        :rtype: bool
        """
        
        return self.list.active == self.index

    def name(self):
        """
        Returns the name for this list element.

        :rtype: str
        """

        return self.list.getAttr(f'list[{self.index}].name')

    def setName(self, name):
        """
        Updates the name for this list element.

        :type name: str
        :rtype: None
        """

        self.list.setAttr(f'list[{self.index}].name', name)

    def absolute(self):
        """
        Returns the `absolute` flag for this list element.

        :rtype: bool
        """

        return self.list.getAttr(f'list[{self.index}].absolute')

    def setAbsolute(self, absolute):
        """
        Updates the `absolute` flag for this list element.

        :type absolute: bool
        :rtype: None
        """

        self.list.setAttr(f'list[{self.index}].absolute', absolute)

    def weight(self):
        """
        Returns the weight for this list element.

        :rtype: float
        """

        return self.list.getAttr(f'list[{self.index}].weight')

    def setWeight(self, weight):
        """
        Updates the weight for this list element.

        :type weight: float
        :rtype: None
        """

        self.list.setAttr(f'list[{self.index}].weight', weight)

    def value(self):
        """
        Returns the value for this list element.

        :rtype: Tuple[float, float, float]
        """

        return self.list.getAttr(f'list[{self.index}].{self.__attributes__[self.list.typeName]}')

    def setValue(self, value):
        """
        Updates the value for this list element.

        :type value: Tuple[float, float, float]
        :rtype: None
        """

        self.list.setAttr(f'list[{self.index}].{self.__attributes__[self.list.typeName]}', value)

    def source(self):
        """
        Returns the source connections from the value plug.
        If a child has no connection then a null plug will be returned instead.

        :rtype: Tuple[om.MPlug, om.MPlug, om.MPlug]
        """

        plug = self.list[f'list[{self.index}].{self.__attributes__[self.list.typeName]}']
        childCount = plug.numChildren()

        childPlugs = [plug.child(i).source() for i in range(childCount)]

        if self.isActive():

            return [childPlug.source() for childPlug in childPlugs]

        else:

            return childPlugs

    def setSource(self, source):
        """
        Updates the source plugs from the value plug.

        :type source: Tuple[om.MPlug, om.MPlug, om.MPlug]
        :rtype: None
        """

        # Check if source is valid
        #
        if stringutils.isNullOrEmpty(source):

            return

        # Iterate through source plugs
        #
        plug = self.list[f'list[{self.index}].{self.__attributes__[self.list.typeName]}']

        for (i, otherChild) in enumerate(source):

            child = plug.child(i)

            if not child.isNull and not otherChild.isNull:

                self.list.connectPlugs(otherChild, child)

            else:

                self.list.breakConnections(child, source=True, destination=False)
    # endregion
