import maya.cmds as mc
import maya.api.OpenMaya as om

from abc import ABCMeta
from collections import deque

from . import pymixin
from .. import mpyattribute
from ..utilities import attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PyTreeMixin(pymixin.PyMixin, metaclass=ABCMeta):
    """
    Overload of PyMixin used to create a parent/child interface for meta nodes.
    """

    parent = mpyattribute.MPyAttribute('parent')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent methods
        #
        super(PyTreeMixin, self).__init__(*args, **kwargs)

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', None)

        if parent is not None:

            self.parent = parent

    def createUserAttributes(self):
        """
        Assigns any user attributes required for data storage.

        :rtype dict[str:om.MObject]
        """

        # Call parent method
        #
        attributes = super(PyTreeMixin, self).createUserAttributes()

        # Create user attributes
        #
        filePath = self.pyFactory.getAttributeTemplate('pytreemixin')
        attributes.update(attributeutils.applyAttributeTemplate(self.object(), filePath))

        return attributes

    @parent.validateAndGetValue
    def parent(self, value):
        """
        Validates any getter requests made to the parent attribute.

        :type value: om.MObject
        :rtype: PyTreeMixin
        """

        # Check for null objects
        #
        if not value.isNull():

            return self.pyFactory(value)

        else:

            return None

    @parent.validateAndSetValue
    def parent(self, value):
        """
        Validates any setter requests made to the parent attribute.

        :type value: Union[om.MObject, PyTreeMixin]
        :rtype: om.MObject
        """

        # Inspect value type
        #
        if isinstance(value, PyTreeMixin):

            return value.object()

        else:

            return value

    def hasParent(self):
        """
        Checks if this node has a valid parent.

        :rtype: bool
        """

        return self.parent is not None

    def iterParents(self):
        """
        Returns a generator that iterates over all the parents relative to this node.

        :rtype: iter
        """

        parent = self.parent

        while parent is not None:

            yield parent
            parent = parent.parent

    def parents(self):
        """
        Returns a list of parents relative to this instance.

        :rtype: list[PyTreeMixin]
        """

        return list(self.iterParents())

    def topLevelParent(self):
        """
        Returns the top level parent relative to this node.
        If this node is already the top most parent then itself is returned.

        :rtype: PyTreeMixin
        """

        parents = self.parents()
        numParents = len(parents)

        if numParents > 0:

            return parents[-1]

        else:

            return self

    def findAncestors(self, T):
        """
        Returns a list of ancestors that are an instance of the given type name.

        :type T: type
        :rtype: list[pymixin.PyMixin]
        """

        return [x for x in self.iterParents() if isinstance(x, T)]

    def iterChildren(self):
        """
        Returns a generator that iterates over all of the children relative to this node.

        :rtype: iter
        """

        # Iterate through destination plugs
        #
        plug = self.findPlug('message')  # type: om.MPlug
        destinations = plug.destinations()  # type: list[om.MPlug]

        for destination in destinations:

            # Check if plug is derived from pyNode
            #
            node = destination.node()
            typeName = om.MFnDependencyNode(node).typeName
            plugName = destination.partialName(useLongNames=True)

            if typeName == self.__plugin__ and plugName == 'parent':

                yield self.pyFactory(node)

            else:

                continue

    def children(self):
        """
        Returns a list of children relative to this node.

        :rtype: list[PyTreeMixin]
        """

        return list(self.iterChildren())

    def siblings(self):
        """
        Returns a generator that iterates over all of the siblings relative to this node.

        :rtype: iter
        """

        if self.hasParent():

            return [x for x in self.parent.iterChildren() if x is not self]

        else:

            return []

    def iterDescendants(self):
        """
        Returns a generator that iterated over all of the descendants relative to this node.

        :rtype: iter
        """

        queue = deque(self.children())

        while len(queue) > 0:

            descendant = queue.popleft()
            yield descendant

            queue.extend(descendant.children())

    def findDescendants(self, T):
        """
        Returns a list of descendants that are an instance of the given type name.

        :type T: type
        :rtype: list[PyTreeMixin]
        """

        return [x for x in self.iterDescendants() if isinstance(x, T)]
