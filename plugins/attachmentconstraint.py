from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..builtins import constraintmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AttachmentConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with attachment constraints.
    """

    # region Dunderscores
    __plugin__ = 'attachmentConstraint'

    __targets__ = {
        'targetMesh': 'worldMesh'
    }

    __inputs__ = {
        'constraintRotateOrder': 'rotateOrder',
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ',
        'constraintRotateX': 'rotateX',
        'constraintRotateY': 'rotateY',
        'constraintRotateZ': 'rotateZ'
    }
    # endregion

    # region Attributes
    relative = mpyattribute.MPyAttribute('relative')
    offsetTranslate = mpyattribute.MPyAttribute('offsetTranslate')
    offsetTranslateX = mpyattribute.MPyAttribute('offsetTranslateX')
    offsetTranslateY = mpyattribute.MPyAttribute('offsetTranslateY')
    offsetTranslateZ = mpyattribute.MPyAttribute('offsetTranslateZ')
    offsetRotate = mpyattribute.MPyAttribute('offsetRotate')
    offsetRotateX = mpyattribute.MPyAttribute('offsetRotateX')
    offsetRotateY = mpyattribute.MPyAttribute('offsetRotateY')
    offsetRotateZ = mpyattribute.MPyAttribute('offsetRotateZ')
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
    restRotate = mpyattribute.MPyAttribute('restRotate')
    restRotateX = mpyattribute.MPyAttribute('restRotateX')
    restRotateY = mpyattribute.MPyAttribute('restRotateY')
    restRotateZ = mpyattribute.MPyAttribute('restRotateZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        raise NotImplementedError()
    # endregion
