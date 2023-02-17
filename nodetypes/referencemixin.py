import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from six import string_types
from dcc.maya.libs import dagutils
from . import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ReferenceMixin(dependencymixin.DependencyMixin):
    """
    Overload of `DependencyMixin` that interfaces with reference nodes.
    """

    # region Dunderscores
    __api_type__ = om.MFn.kReference

    def __contains__(self, item):
        """
        Private method called to determine if this instance contains the given item.

        :type item: Union[str, om.MObject, om.MDagPath]
        :rtype: bool
        """

        return self.containsNodeExactly(dagutils.getMObject(item))
    # endregion

    # region Methods
    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnReference
        """

        return super(ReferenceMixin, self).functionSet()

    def isValid(self):
        """
        Evaluates whether this skeleton is valid.

        :rtype: bool
        """

        return os.path.exists(self.filePath())

    def getAssociatedReferenceNode(self):
        """
        Overloaded used to retrieve the reference this instance belongs to.
        This overload ignores the parent method since we know this is already a reference node.

        :rtype: Reference
        """

        return self

    def containsNodeExactly(self, dependNode):
        """
        Method used to determine if this reference contains the supplied node.

        :type dependNode: om.MObject
        :rtype: bool
        """

        return self.functionSet().containsNodeExactly(dependNode)

    def nodes(self):
        """
        Returns the nodes that belong to this reference.

        :rtype: list[om.MObject]
        """

        return self.functionSet().nodes()

    def getNodeByName(self, name):
        """
        Returns a referenced node based on the supplied name.

        :type name: str
        :rtype: DependencyMixin
        """
        return self.scene('{namespace}:{name}'.format(namespace=self.namespace(), name=name))

    def getNodeByUuid(self, uuid):
        """
        Returns a referenced node based on the supplied UUID.

        :type uuid: Union[str, om.MUuid]
        :rtype: DependencyMixin
        """

        # Check if uuid requires initializing
        #
        if isinstance(uuid, string_types):

            uuid = om.MUuid(uuid)

        # Collect nodes by UUID
        #
        found = dagutils.getMObjectByMUuid(uuid)

        if isinstance(found, om.MObject):

            return self.scene(found)

        elif isinstance(found, (list, tuple)):

            # Collect nodes that belong to this reference
            #
            nodes = [x for x in found if x in self]
            numNodes = len(nodes)

            if numNodes == 0:

                return None

            elif numNodes == 1:

                return self.scene(nodes[0])

            else:

                raise TypeError('getNodeByUuid() expects a unique UUID (%s given)!' % uuid)

        else:

            return None

    def filePath(self, resolvedName=True, includePath=True, includeCopyNumber=False):
        """
        Returns the file path  associated with this reference.
        FIXME: Under the hood Maya is negating the `includePath` variable?

        :param resolvedName: Determines if the original user supplied value should be returned.
        :param includePath: Determines if the path to the file should be returned.
        :param includeCopyNumber: Determines if the copy number should be included.
        :rtype: str
        """

        return self.functionSet().fileName(resolvedName, not includePath, includeCopyNumber)

    def setFilePath(self, filePath):
        """
        Updates the file path associated with this reference.

        :type filePath: str
        :rtype: None
        """

        mc.file(filePath, loadReference=self.name())

    def parentReference(self):
        """
        Returns the parent of this reference.

        :rtype: Reference
        """

        return self.scene(self.functionSet().parentReference())

    def reload(self):
        """
        Reloads this reference.
        Kinda surprising there's no API hook for this?

        :rtype: None
        """

        mc.file(referenceNode=self.name(), loadReference=True)

    def referenceEdits(self):
        """
        Returns a list of edits made to this reference.

        :rtype: list[str]
        """

        return mc.file(query=True, referenceNode=self.name(), editCommand=True)

    def cleanReference(self):
        """
        Removes all edits from this reference.

        :rtype: None
        """
        
        pass
    # endregion
