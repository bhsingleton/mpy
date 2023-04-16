from maya.api import OpenMaya as om
from dcc.maya.libs import transformutils
from .. import mpyattribute
from ..nodetypes import constraintmixin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PositionConstraintMixin(constraintmixin.ConstraintMixin):
    """
    Overload of `ConstraintMixin` that interfaces with position constraints.
    """

    # region Dunderscores
    __plugin__ = 'positionConstraint'

    __targets__ = {
        'targetMatrix': 'matrix',
        'targetParentMatrix': 'parentMatrix',
    }

    __inputs__ = {
        'constraintParentInverseMatrix': 'parentInverseMatrix'
    }

    __outputs__ = {
        'constraintTranslateX': 'translateX',
        'constraintTranslateY': 'translateY',
        'constraintTranslateZ': 'translateZ'
    }
    # endregion

    # region Attributes
    localOrWorld = mpyattribute.MPyAttribute('localOrWorld')
    relative = mpyattribute.MPyAttribute('relative')
    offsetTranslate = mpyattribute.MPyAttribute('offsetTranslate')
    offsetTranslateX = mpyattribute.MPyAttribute('offsetTranslateX')
    offsetTranslateY = mpyattribute.MPyAttribute('offsetTranslateY')
    offsetTranslateZ = mpyattribute.MPyAttribute('offsetTranslateZ')
    restTranslate = mpyattribute.MPyAttribute('restTranslate')
    restTranslateX = mpyattribute.MPyAttribute('restTranslateX')
    restTranslateY = mpyattribute.MPyAttribute('restTranslateY')
    restTranslateZ = mpyattribute.MPyAttribute('restTranslateZ')
    # endregion

    # region Methods
    def maintainOffset(self):
        """
        Ensures the constraint object's transform matches the rest matrix.

        :rtype: None
        """

        # Temporarily disable offset
        #
        self.relative = False

        # Calculate offset
        #
        constraintMatrix = self.getAttr('constraintMatrix')
        restMatrix = self.restMatrix()

        offsetMatrix = restMatrix * constraintMatrix.inverse()
        offsetTranslate = transformutils.breakMatrix(offsetMatrix)[3]

        # Update re-enable offset
        #
        self.offsetTranslate = offsetTranslate
        self.relative = True
    # endregion
