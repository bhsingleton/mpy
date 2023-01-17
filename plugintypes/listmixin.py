from maya.api import OpenMaya as om
from six.moves import collections_abc
from .. import mpyattribute
from ..nodetypes import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractListMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with list nodes.
    """

    # region Attributes
    active = mpyattribute.MPyAttribute('active')
    average = mpyattribute.MPyAttribute('average')
    # endregion

    # region Dunderscores
    __plugin__ = 'abstractList'
    __value_attribute__ = None  # Used to initialize ListElement instances!
    # endregion

    # region Methods
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

            yield ListElement(self, index=i, attribute=self.__value_attribute__)

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

            return None
    # endregion


class PositionListMixin(AbstractListMixin):
    """
    Overload of `AbstractListMixin` that interfaces with `positionList` nodes.
    """

    # region Dunderscores
    __plugin__ = 'positionList'
    __value_attribute__ = 'position'
    # endregion


class RotationListMixin(AbstractListMixin):
    """
    Overload of `AbstractListMixin` that interfaces with `rotationList` nodes.
    """

    # region Dunderscores
    __plugin__ = 'rotationList'
    __value_attribute__ = 'rotation'
    # endregion


class ScaleListMixin(AbstractListMixin):
    """
    Overload of `AbstractListMixin` that interfaces with `scaleList` nodes.
    """

    # region Dunderscores
    __plugin__ = 'scaleList'
    __value_attribute__ = 'scale'
    # endregion


class ListElement(object):
    """
    Base class used to interface with list elements.
    """

    # region Dunderscores
    __slots__ = ('_list', '_index', '_attribute')

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
        self._attribute = kwargs.get('attribute', '')

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

    @property
    def attribute(self):
        """
        Getter method that returns the attribute name for the list element's value.

        :rtype: str
        """

        return self._attribute
    # endregion

    # region Methods
    def listPlug(self):
        """
        Returns the plug element associated with this list element.

        :rtype: om.MPlug
        """

        return self.list.findPlug('list[{index}]'.format(index=self.index))

    def targetChildPlug(self, name):
        """
        Returns a child plug from the associated plug element.

        :type name: str
        :rtype: om.MPlug
        """

        return self.listPlug().child(self.list.attribute(name))

    def name(self):
        """
        Returns the name for this list element.

        :rtype: str
        """

        return self.targetChildPlug('name').asString()

    def setName(self, name):
        """
        Updates the name for this list element.

        :type name: str
        :rtype: None
        """

        self.targetChildPlug('name').setString(name)

    def absolute(self):
        """
        Returns the `absolute` flag for this list element.

        :rtype: bool
        """

        return self.targetChildPlug('absolute').asBool()

    def setAbsolute(self, absolute):
        """
        Updates the `absolute` flag for this list element.

        :type absolute: bool
        :rtype: None
        """

        return self.targetChildPlug('absolute').setBool(absolute)

    def weight(self):
        """
        Returns the weight for this list element.

        :rtype: float
        """

        return self.targetChildPlug('weight').asFloat()

    def setWeight(self, weight):
        """
        Updates the weight for this list element.

        :type weight: float
        :rtype: None
        """

        return self.targetChildPlug('weight').setFloat(weight)

    def value(self):
        """
        Returns the value for this list element.

        :rtype: List[float]
        """

        self.list.getAttr('list[{index}].{attribute}'.format(index=self.index, attribute=self.attribute))

    def setValue(self, value):
        """
        Updates the value for this list element.

        :type value: List[float]
        :rtype: None
        """

        self.list.setAttr('list[{index}].{attribute}'.format(index=self.index, attribute=self.attribute), value)
    # endregion
