from maya import cmds as mc
from maya.api import OpenMaya as om

from . import dependencymixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DeformerMixin(dependencymixin.DependencyMixin):
    """
    Overload of DependencyMixin used to interface with deformer nodes inside the scene file.
    """

    __apitype__ = om.MFn.kGeometryFilt

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(DeformerMixin, self).__init__(*args, **kwargs)

    def __len__(self):
        """
        Private method that evaluates the number of control points this deformer affects.

        :rtype: int
        """

        return self.intermediateObject().numControlPoints()

    def transform(self):
        """
        Returns the transform node associated with the deformed shape node.

        :rtype: mpynode.nodetypes.transformmixin.TransformMixin
        """

        return self.shape().parent()

    def shape(self):
        """
        Returns the deformed shape node associated with this deformer.

        :rtype: mpynode.nodetypes.meshmixin.MeshMixin
        """

        return self.dependents(apiType=om.MFn.kShape)[0]

    def intermediateObject(self):
        """
        Returns the base shape node associated with this deformer.

        :rtype: mpynode.nodetypes.meshmixin.MeshMixin
        """

        return self.dependsOn(apiType=om.MFn.kShape)[0]

    def numControlPoints(self):
        """
        Method used to determine the number of control points this deformer affects.

        :rtype: int
        """

        return self.intermediateObject().numControlPoints()

    @property
    def envelope(self):
        """
        Property method used to retrieve the current envelope value associated with this instance.

        :rtype: float
        """

        return self.getAttr('envelope')

    @envelope.setter
    def envelope(self, envelope):
        """
        Setter method used to assign a new float value to this plug.

        :type envelope: float
        :rtype: None
        """

        self.setAttr('envelope', envelope)

    def objectSet(self):
        """
        Returns the component object set associated with this deformer.

        :rtype: DependencyMixin
        """

        # Collect all object sets
        #
        objectSets = [x for x in self.findPlug('message').destinations() if x.node().hasFn(om.MFn.kSet)]
        numObjectSets = len(objectSets)

        if numObjectSets == 1:

            return dependencymixin.DependencyMixin(objectSets[0].node())

        else:

            raise TypeError('Unable to locate object set associated with "%s" deformer!' % self.name())

    def dagSetMembers(self):
        """
        Method used to collect all of the dag set members associated with this deformer.
        Each item returned will contain a dictionary with the following values:
            'objectGrpCompList': List of vertex indices that will be deformed.
            'objectGroupId': The unique group id assigned to this deformer.
            'objectGrpColor': The wireframe colour assigned to deformed mesh.

        :rtype: list
        """

        # Get object set
        #
        objectSet = self.objectSet()

        # Get connected object group
        #
        plug = objectSet.findPlug('dagSetMembers')

        indices = plug.getExistingArrayAttributeIndices()
        numIndices = len(indices)

        members = [None] * numIndices

        for physicalIndex, logicalIndex in enumerate(indices):

            # Get source plug from element
            #
            plug.selectAncestorLogicalIndex(logicalIndex)
            source = plug.source()

            objectGroup = {}

            # Get group components
            #
            fnDependencyNode = om.MFnDependencyNode(source.node())
            objectGroupCompListPlug = source.child(fnDependencyNode.attribute('objectGrpCompList'))

            fnComponentListData = om.MFnComponentListData(objectGroupCompListPlug.asMObject())
            numComponents = fnComponentListData.length()

            objectGroup['objectGrpCompList'] = []

            for i in range(numComponents):

                fnSingleIndexedComponent = om.MFnSingleIndexedComponent(fnComponentListData.get(i))
                objectGroup['objectGrpCompList'].extend(fnSingleIndexedComponent.getElements())

            # Get group ID
            #
            objectGroupIdPlug = source.child(fnDependencyNode.attribute('objectGroupId'))
            objectGroup['objectGroupId'] = objectGroupIdPlug.asInt()

            # Get group color
            #
            objectGroupColorPlug = source.child(fnDependencyNode.attribute('objectGrpColor'))
            objectGroup['objectGrpColor'] = objectGroupColorPlug.asInt()

            members[physicalIndex] = objectGroup

        return members
