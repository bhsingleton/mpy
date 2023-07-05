import inspect

from dcc.maya.libs import attributeutils
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

    # region Methods
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
    def getUserAttributeDefinition(cls):
        """
        Returns the attribute definition for this extension class.
        All attributes are nested under a compound metadata attribute!

        :rtype: Dict[str, Any]
        """

        # Iterate through bases
        #
        definition = {'longName': 'metadata', 'attributeType': 'compound', 'children': []}

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

                # Create child-attribute definition
                #
                childDefinition = {'longName': value.name, 'shortName': value.name}
                childDefinition.update(value.constructors)

                definition['children'].append(childDefinition)

        return definition

    def ensureUserAttributes(self):
        """
        Ensures that the user attributes exist on this node.

        :rtype: None
        """

        # Merge missing attributes
        #
        definition = self.getUserAttributeDefinition()
        attributeutils.addAttribute(self.object(), **definition)

        # Update extension pointers
        #
        self.extensionName = self.__class__.__bases__[-1].__name__
        self.extensionPath = self.__class__.__bases__[-1].__module__
    # endregion
