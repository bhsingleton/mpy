from maya.api import OpenMaya as om
from . import transformmixin
from .. import mpyattribute

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class IKHandleMixin(transformmixin.TransformMixin):
    """
    Overload of `TransformMixin` that interfaces with IK-handles.
    """

    # region Attributes
    endEffector = mpyattribute.MPyAttribute('endEffector')
    ikFkManipulation = mpyattribute.MPyAttribute('ikFkManipulation')
    dForwardAxis = mpyattribute.MPyAttribute('dForwardAxis')
    ikSolver = mpyattribute.MPyAttribute('ikSolver')
    ikBlend = mpyattribute.MPyAttribute('ikBlend')
    inCurve = mpyattribute.MPyAttribute('inCurve')
    offset = mpyattribute.MPyAttribute('offset')
    poWeight = mpyattribute.MPyAttribute('poWeight')
    poleVector = mpyattribute.MPyAttribute('poleVector')
    poleVectorX = mpyattribute.MPyAttribute('poleVectorX')
    poleVectorY = mpyattribute.MPyAttribute('poleVectorY')
    poleVectorZ = mpyattribute.MPyAttribute('poleVectorZ')
    priority = mpyattribute.MPyAttribute('priority')
    roll = mpyattribute.MPyAttribute('roll')
    rootOnCurve = mpyattribute.MPyAttribute('rootOnCurve')
    rootTwistMode = mpyattribute.MPyAttribute('rootTwistMode')
    snapEnable = mpyattribute.MPyAttribute('snapEnable')
    startJoint = mpyattribute.MPyAttribute('startJoint')
    stickiness = mpyattribute.MPyAttribute('stickiness')
    twist = mpyattribute.MPyAttribute('twist')
    dTwistControlEnable = mpyattribute.MPyAttribute('dTwistControlEnable')
    dTwistRamp = mpyattribute.MPyAttribute('dTwistRamp')
    dTwistRampMult = mpyattribute.MPyAttribute('dTwistRampMult')
    dTwistStartEnd = mpyattribute.MPyAttribute('dTwistStartEnd')
    twistType = mpyattribute.MPyAttribute('twistType')  # 0=Linear, 1=EaseIn, 2=EaseOut, 3=EaseInOut
    dTwistValueType = mpyattribute.MPyAttribute('dTwistValueType')  # 0=Total, 1=Start/End, 2=Ramp
    weight = mpyattribute.MPyAttribute('weight')
    dWorldUpAxis = mpyattribute.MPyAttribute('dWorldUpAxis')
    dWorldUpMatrix = mpyattribute.MPyAttribute('dWorldUpMatrix')
    dWorldUpMatrixEnd = mpyattribute.MPyAttribute('dWorldUpMatrixEnd')
    dWorldUpType = mpyattribute.MPyAttribute('dWorldUpType')  # 0=Scene Up, 1=Object Up, 2=Object Up (Start/End), 3=Object Rotation Up, 4=Object Rotation Up (Start/End), 5=Vector, 6=Vector (Start/End), 7=Relative
    dWorldUpVector = mpyattribute.MPyAttribute('dWorldUpVector')
    dWorldUpVectorX = mpyattribute.MPyAttribute('dWorldUpVectorX')
    dWorldUpVectorY = mpyattribute.MPyAttribute('dWorldUpVectorY')
    dWorldUpVectorZ = mpyattribute.MPyAttribute('dWorldUpVectorZ')
    dWorldUpVectorEnd = mpyattribute.MPyAttribute('dWorldUpVectorEnd')
    dWorldUpVectorEndX = mpyattribute.MPyAttribute('dWorldUpVectorEndX')
    dWorldUpVectorEndY = mpyattribute.MPyAttribute('dWorldUpVectorEndY')
    dWorldUpVectorEndZ = mpyattribute.MPyAttribute('dWorldUpVectorEndZ')
    # endregion

    # region Dunderscores
    __api_type__ = om.MFn.kIkHandle
    # endregion
