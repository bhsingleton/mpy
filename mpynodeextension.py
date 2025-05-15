import inspect

from maya.api import OpenMaya as om
from dcc.maya.libs import attributeutils, plugutils
from itertools import chain
from . import mpynode, mpyattribute
from .abstract import mabcmeta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyNodeExtension(mpynode.MPyNode, metaclass=mabcmeta.MABCMeta):
    """
    Overload of `MPyNode` that serves as a base class for extension interfaces.
    """

    # region Attributes
    extensionName = mpyattribute.MPyAttribute('__class__', attributeType='str')
    extensionPath = mpyattribute.MPyAttribute('__module__', attributeType='str')
    # endregion

    # region Dunderscores
    __attribute_exceptions__ = ('notes', 'attributeAliasList')

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been initialized.

        :rtype: None
        """

        # Call parent method
        #
        super(MPyNodeExtension, self).__post_init__(*args, **kwargs)

        # Ensure extension attributes exist
        #
        log.debug(f'Creating "{self.__class__.__name__}" extension attributes!')
        self.ensureUserAttributes()
    # endregion

    @classmethod
    def create(cls, typeName, name='', parent=None, skipSelect=True):
        """
        Returns a new dependency node of the specified type with this extension.

        :type typeName: str
        :type name: Union[str, Dict[str, Any]]
        :type parent: Union[str, om.MObject, om.MDagPath, MPyNode]
        :type skipSelect: bool
        :rtype: MPyNodeExtension
        """

        # Call parent method
        # Add this extension class to node
        #
        node = super(MPyNodeExtension, cls).create(typeName, name=name, parent=parent, skipSelect=skipSelect)
        node.addExtension(cls)

        return node

    @classmethod
    def iterBases(cls):
        """
        Returns a generator that yields parent classes.
        This generator starts from the top-level base class and works its way to this class!

        :rtype: Iterator[Callable]
        """

        return reversed(inspect.getmro(cls))

    @classmethod
    def bases(cls):
        """
        Returns a list of parent classes.

        :rtype: List[Callable]
        """

        return tuple(cls.iterBases())

    @classmethod
    def getUserAttributeDefinition(cls):
        """
        Returns the attribute definition for this extension class.
        Each attribute is categorizing by its associated extension class.

        :rtype: List[Dict[str, Any]]
        """

        # Iterate through bases
        #
        definitions = []

        for base in cls.iterBases():

            # Iterate through class members
            #
            for (key, value) in base.__dict__.items():

                # Check if this is an attribute
                #
                if not isinstance(value, mpyattribute.MPyAttribute):

                    continue

                # Check if attribute has any constructors
                #
                numConstructors = len(value.constructors)

                if numConstructors == 0:

                    continue

                # Create attribute definition
                #
                definition = {'longName': value.name, 'shortName': value.name, 'category': base.__name__}
                definition.update(value.constructors)

                # Check if any attributes require nesting
                #
                children = definition.pop('children', [])
                hasChildren = len(children) > 0

                if hasChildren:

                    indices = [i for (i, definition) in enumerate(definitions) if definition['longName'] in children]
                    children = [definitions.pop(i) for i in reversed(indices)]

                    definition['children'] = tuple(reversed(children))  # This will prevent the JSON decoder from crashing!

                definitions.append(definition)

        return definitions

    def findDeprecatedAttributes(self):
        """
        Returns a list of deprecated attributes.

        :rtype: List[om.MObject]
        """

        # Collect accepted user attributes
        #
        attributeDefinition = self.getUserAttributeDefinition()

        accepted = []
        accepted.extend([spec['longName'] for spec in attributeDefinition])
        accepted.extend(list(chain(*[[subspec['longName'] for subspec in spec.get('children', [])] for spec in attributeDefinition])))

        # Filter out deprecated attributes
        #
        fnAttribute = om.MFnAttribute()
        deprecated = []

        for attribute in self.listAttr(userDefined=True):

            fnAttribute.setObject(attribute)
            isAccepted = fnAttribute.name in accepted
            isException = fnAttribute.name in self.__attribute_exceptions__

            if not (isAccepted or isException):

                deprecated.append(attribute)

            else:

                continue

        return deprecated

    def removeDeprecatedAttributes(self):
        """
        Removes any deprecated attributes from this node.

        :rtype: None
        """

        # Iterate through known attributes
        #
        deprecatedAttributes = self.findDeprecatedAttributes()

        for attribute in deprecatedAttributes:

            # Break any connections
            #
            plug = self.findPlug(attribute)
            plugutils.breakConnections(plug)

            # Remove attribute from node
            #
            log.info(f'Removing deprecated attribute: {plug.info}')
            self.removeAttr(attribute)

    def ensureUserAttributes(self):
        """
        Ensures that all required user attributes exist on this node.

        :rtype: None
        """

        # Check if node is referenced
        #
        if self.isFromReferencedFile:

            return  # We don't want any unnecessary reference edits!

        # Remove deprecated attributes
        #
        self.removeDeprecatedAttributes()

        # Merge missing attributes
        #
        attributeDefinition = self.getUserAttributeDefinition()

        for attributeSpec in attributeDefinition:

            attributeutils.addAttribute(self.object(), **attributeSpec)

        # Update extension pointers
        #
        self.extensionName = self.__class__.__bases__[-1].__name__
        self.extensionPath = self.__class__.__bases__[-1].__module__

        self.lockAttr('__class__', '__module__')

    def revertUserAttributes(self):
        """
        Reverts any user attributes associated with this extension.

        :rtype: None
        """

        attributeDefinition = self.getUserAttributeDefinition()

        for attributeSpec in attributeDefinition:

            attributeName = attributeSpec['longName']
            hasAttribute = self.hasAttr(attributeName)

            if not hasAttribute:

                continue

            attribute = self.attribute(attributeName)
            self.removeAttr(attribute)
    # endregion
