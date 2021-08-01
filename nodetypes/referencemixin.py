import maya.cmds as mc
import maya.api.OpenMaya as om

from six import string_types

from . import dependencymixin
from ..utilities import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ReferenceMixin(dependencymixin.DependencyMixin):
    """
    Overload of DependencyMixin used to interface with reference nodes.
    """

    __apitype__ = om.MFn.kReference

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(ReferenceMixin, self).__init__(*args, **kwargs)

    def __contains__(self, item):
        """
        Private method called to determine if this instance contains the given item.

        :type item: Union[str, om.MObject, om.MDagPath]
        :rtype: bool
        """

        return self.containsNodeExactly(dagutils.getMObject(item))

    def functionSet(self):
        """
        Returns a function set compatible with this object.

        :rtype: om.MFnReference
        """

        return super(ReferenceMixin, self).functionSet()

    def reference(self):
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

    def getNodeByUuid(self, uuid):
        """
        Returns a referenced node based on the supplied UUID.
        This overload ignores the parent method since we're only concerned about the referenced nodes.

        :type uuid: Union[str, om.MUuid]
        :rtype: DependencyNode
        """

        # Check if uuid requires initializing
        #
        if isinstance(uuid, string_types):

            uuid = om.MUuid(uuid)

        # Collect nodes by UUID
        #
        found = dagutils.getMObjectByMUuid(uuid)

        if isinstance(found, om.MObject):

            # Initialize node interface
            #
            return self.pyFactory(found)

        elif isinstance(found, list):

            # Collect nodes that belong to this reference
            #
            nodes = [x for x in found if x in self]
            numNodes = len(nodes)

            if numNodes == 0:

                return None

            elif numNodes == 1:

                return self.pyFactory(nodes[0])

            else:

                raise TypeError('getNodeByUuid() expects a unique UUID (%s given)!' % uuid)

        else:

            return None

    def filePath(self, resolvedName=False, includePath=False, includeCopyNumber=False):
        """
        Returns the file path  associated with this reference.
        FIXME: Under the hood Maya is negating the includePath variable?

        :param resolvedName: Determines if the original user supplied value should be returned.
        :param includePath: Determines if the path to the file should be returned.
        :param includeCopyNumber: Determines if the copy number should be included.
        :rtype: str
        """

        return self.functionSet().fileName(resolvedName, includePath, includeCopyNumber)

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

        return self.pyFactory(self.functionSet().parentReference())

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
