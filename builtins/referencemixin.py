import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.maya.libs import dagutils
from dcc.vendor.six import string_types
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

    @dependencymixin.DependencyMixin.isLocked.setter
    def isLocked(self, isLocked):
        """
        Setter method used to change the lock state on this node.

        :type isLocked: bool
        :rtype: None
        """

        om.MFnDependencyNode(self.object()).isLocked = isLocked  # Bypasses lock restrictions on `MFnReference` function set!

    def isValid(self):
        """
        Evaluates whether this reference is valid.

        :rtype: bool
        """

        return os.path.exists(self.filePath())

    def isAlive(self):
        """
        Evaluates whether this reference is still alive.

        :rtype: bool
        """

        try:

            return not stringutils.isNullOrEmpty(self.filePath()) and super(ReferenceMixin, self).isAlive()

        except RuntimeError as exception:

            return False

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

        :rtype: List[om.MObject]
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

    def setFilePath(self, filePath, clearEdits=False):
        """
        Updates the file path associated with this reference.

        :type filePath: str
        :type clearEdits: bool
        :rtype: None
        """

        # Check if reference is loaded
        #
        isLoaded = self.isLoaded()

        if isLoaded:

            # Check if edits should be removed
            #
            if clearEdits:

                self.unload()
                self.clearEdits()

            # Update file path
            #
            mc.file(filePath, loadReference=self.absoluteName())

        else:

            # Check if edits should be removed
            #
            if clearEdits:

                self.clearEdits()

            # Update file path
            #
            mc.file(filePath, unloadReference=self.absoluteName())

    def associatedNamespace(self, shortName=False):
        """
        Returns the namespace for the referenced nodes.

        :type shortName: bool
        :rtype: str
        """

        if self.isLoaded():

            return self.functionSet().associatedNamespace(shortName)

        else:

            return self.name().rstrip('RN')  # Without the reference being loaded this is our only fallback...

    def setAssociatedNamespace(self, namespace):
        """
        Updates the namespace for the referenced nodes.

        :type namespace: str
        :rtype: bool
        """

        # Check if referenced is loaded
        #
        if not self.isLoaded():

            log.warning('References must be loaded in order to be renamed!')
            return False

        # Check if this is a top-level reference
        #
        if not self.isTopLevelReference():

            log.warning('References must be top-level in order to be renamed!')
            return False

        # Redundancy check
        #
        newNamespace = namespace.replace('RN', '')
        oldNamespace = self.associatedNamespace()

        isRedundant = (oldNamespace == newNamespace)
        isEmpty = stringutils.isNullOrEmpty(newNamespace)

        if isRedundant or isEmpty:

            return False

        # Check if namespace change is valid
        #
        namespaceExists = om.MNamespace.namespaceExists(oldNamespace)
        namespaceAvailable = not om.MNamespace.namespaceExists(newNamespace)

        if namespaceExists and namespaceAvailable:

            # Rename namespace
            #
            mc.file(
                self.filePath(resolvedName=False),
                edit=True,
                referenceNode=self.name(includeNamespace=True),
                namespace=newNamespace
            )

            # Rename reference node
            #
            self.unlock()
            self.setName(f'{newNamespace}RN')
            self.lock()

            return True

        else:

            log.warning(f'Unable to rename namespace "{oldNamespace}" > "{newNamespace}"')
            return False

    def isTopLevelReference(self):
        """
        Evaluates if this is a top-level reference.

        :rtype: bool
        """

        return self.functionSet().parentReference().isNull()

    def parentReference(self):
        """
        Returns the parent of this reference.

        :rtype: Union[ReferenceMixin, None]
        """

        return self.scene(self.functionSet().parentReference())

    def load(self, loadReferenceDepth='asPrefs'):
        """
        Loads this reference into the current scene file.

        :type loadReferenceDepth: str
        :rtype: None
        """

        if not self.isLoaded():

            mc.file(
                self.filePath(resolvedName=False),
                loadReference=self.name(includeNamespace=True),
                loadReferenceDepth=loadReferenceDepth
            )

        else:

            log.debug('Reference is already loaded...')

    def unload(self):
        """
        Unloads this reference from the current scene file.

        :rtype: None
        """

        if self.isLoaded():

            mc.file(
                self.filePath(resolvedName=False),
                unloadReference=self.name(includeNamespace=True)
            )

        else:

            log.debug('Reference is already unloaded...')

    def reload(self):
        """
        Reloads this reference.
        TODO: Investigate if there is an API method for this?

        :rtype: None
        """

        if self.isLoaded():

            self.unload()

        self.load()

    def getEdits(self, successfulEdits=True, failedEdits=False):
        """
        Returns a list of edits made to this reference.

        :type successfulEdits: bool
        :type failedEdits: bool
        :rtype: List[str]
        """

        return mc.referenceQuery(
            self.absoluteName(),
            editStrings=True,
            successfulEdits=successfulEdits,
            failedEdits=failedEdits
        )

    def removeEdits(self, *plugs, editCommand='setAttr', failedEdits=True, successfulEdits=True):
        """
        Removes any reference edits from the specified plugs.

        :type editCommand: str
        :type failedEdits: bool
        :type successfulEdits: bool
        :rtype: None
        """

        for plug in plugs:

            mc.referenceEdit(plug.info, editCommand=editCommand, failedEdits=failedEdits, successfulEdits=successfulEdits, removeEdits=True)

    def clearEdits(self):
        """
        Removes all edits from this reference.

        :rtype: None
        """

        # Check if reference is loaded
        # If so, unload reference to avoid any crashes!
        #
        isLoaded = self.isLoaded()

        if isLoaded:

            self.unload()

        # Remove all reference edits
        #
        mc.referenceEdit(self.absoluteName(), removeEdits=True)

        # Check if reference should be reloaded
        #
        if isLoaded:

            self.load()

    def delete(self):
        """
        Removes this reference from the scene file.

        :rtype: None
        """

        mc.file(self.filePath(), referenceNode=self.name(), removeReference=True)
    # endregion
