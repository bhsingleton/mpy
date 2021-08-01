import maya.cmds as mc
import maya.OpenMaya as legacy
import maya.api.OpenMaya as om

import json
import os
import re

from itertools import chain

from . import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


SHADING_ENGINES = {0: 'C_Controls_SG', 1: 'L_Controls_SG', 2: 'R_Controls_SG', 3: 'C_Controls_SG'}
SURFACE_SHADERS = {0: 'C_Controls_SS', 1: 'L_Controls_SS', 2: 'R_Controls_SS', 3: 'C_Controls_SG'}
COLOUR_RGB = {0: [1.0, 1.0, 0.0], 1: [0.0, 0.0, 1.0], 2: [1.0, 0.0, 0.0], 3: [1.0, 1.0, 0.0]}
COLOR_INDEX = {0: 17, 1: 6, 2: 13, 3: 17}


def getShapesDirectory():
    """
    Returns the curves directory relative to this module.

    :rtype: str
    """

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), r'shapes')


def getShapeFilePath(name):
    """
    Returns the shape file associated with the supplied name from the shapes directory.

    :type name: str
    :rtype: str
    """

    # Concatenate file path
    #
    directory = getShapesDirectory()
    filePath = os.path.join(directory, '{name}.json'.format(name=name))

    # Check if concatenation is valid
    #
    if os.path.exists(filePath):

        return filePath

    else:

        return ''


def loadShape(name):
    """
    Loads the shape data from the given name.

    :type name: str
    :rtype: list
    """

    # Get the shape path from the given name
    #
    filePath = getShapeFilePath(name)

    if os.path.exists(filePath):

        # Load json data
        #
        with open(filePath) as jsonFile:

            return json.load(jsonFile)

    else:

        log.warning('Unable to locate shape: %s' % name)
        return None


def dumpNurbsCurve(curve):
    """
    Dumps the supplied nurbs curve into a json compatible object.
    To call the create method the following parameters are needed:
        controlVertices: MPointArray
        knots: MDoubleArray
        degree: unsigned int
        form: MFNNurbsCurve enumerator
        create2D: bool
        createRational: bool
        parentOrOwner: DAG parent

    :type curve: om.MObject
    :rtype: dict
    """

    # Get nurbs curve parameters
    #
    dagPath = om.MDagPath.getAPathTo(curve)
    fnNurbsCurve = om.MFnNurbsCurve(dagPath)

    data = {
        'apiType': om.MFn.kNurbsSurface,
        'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnNurbsCurve.cvPositions()],
        'knots': [x for x in fnNurbsCurve.knots()],
        'degree': fnNurbsCurve.degree,
        'form': fnNurbsCurve.form,
        'lineWidth': fnNurbsCurve.findPlug('lineWidth', True).asFloat()
    }

    return data


def dumpNurbsTrimSurface(surface):
    """
    Dumps the supplied nurb surface's trimmed boundaries into a json compatible object.
    Please note Autodesk have yet to implement these methods in their newest API!

    :type surface: legacy.MObject
    :rtype: list[dict]
    """

    # Check number of regions
    # If zero then this surface has no trimmed surfaces
    #
    fnNurbsSurface = legacy.MFnNurbsSurface(surface)
    numRegions = fnNurbsSurface.numRegions()

    if numRegions == 0:

        return

    # Iterate through regions
    #
    fnNurbsCurve = legacy.MFnNurbsCurve()
    items = [None] * numRegions

    for region in range(numRegions):

        # Get trim boundary from region
        #
        boundary = legacy.MTrimBoundaryArray()
        fnNurbsSurface.getTrimBoundaries(boundary, region, True)

        numBoundaries = boundary.length()

        for i in range(numBoundaries):

            curveData = boundary.getMergedBoundary(j)
            fnNurbsCurve.setObject(curveData)

            # Get control points
            #
            numCVs = fnNurbsCurve.numCVs()
            controlsPoints = [None] * numCVs

            for j in range(numCVs):

                point = fnNurbsCurve.getCV(j)
                controlsPoints.set([point.x(), point.y(), point.z(), point.w()], j)

            # Get knots
            #
            numKnots = fnNurbsCurve.numKnots()
            knots = [None] * numKnots

            for j in range(numKnots):

                knots.set(fnNurbsCurve.knot(j), j)

            # Commit curve parameters to dictionary
            #
            items[i] = {
                'apiType': om.MFn.kNurbsCurve,
                'controlPoints': controlsPoints,
                'knots': knots,
                'degree': fnNurbsCurve.degree(),
                'form': fnNurbsCurve.form(),
            }

    return items


def dumpNurbsSurface(surface):
    """
    Dumps the supplied nurbs surface into a json compatible object.

    :type surface: om.MObject
    :rtype: dict
    """

    # Get nurbs surface parameters
    #
    dagPath = om.MDagPath.getAPathTo(surface)
    fnNurbsSurface = om.MFnNurbsSurface(dagPath)

    data = {
        'apiType': om.MFn.kNurbsSurface,
        'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnNurbsSurface.cvPositions()],
        'uKnots': [x for x in fnNurbsSurface.knotsInU()],
        'vKnots': [x for x in fnNurbsSurface.knotsInV()],
        'uDegree': fnNurbsSurface.degreeInU,
        'vDegree': fnNurbsSurface.degreeInV,
        'uForm': fnNurbsSurface.formInU,
        'vForm': fnNurbsSurface.formInV,
        'boundaries': dumpNurbsTrimSurface(dagutils.demoteMObject(surface)),
        'precision': fnNurbsSurface.findPlug('curvePrecisionShaded', True).asFloat()
    }

    return data


def dumpMesh(mesh):
    """
    Dumps the supplied mesh into a json compatible object.
    To call the create method the following parameters are needed:
        vertices: MPointArray
        polygonCounts: MIntArray
        polygonConnects: MIntArray
        parentOrOwner: DAG parent

    :type mesh: om.MObject
    :rtype: dict
    """

    # Get mesh parameters
    #
    fnMesh = om.MFnMesh(mesh)

    data = {
        'apiType': om.MFn.kMesh,
        'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnMesh.getPoints()],
        'polygonConnects': [fnMesh.getPolygonVertices(x) for x in range(fnMesh.numPolygons)],
        'polygonCounts': [fnMesh.polygonVertexCount(x) for x in range(fnMesh.numPolygons)],
        'faceVertexNormals': [fnMesh.getFaceVertexNormals(x) for x in range(fnMesh.numPolygons)],
        'edgeSmoothings': [fnMesh.isEdgeSmooth(x) for x in range(fnMesh.numEdges)]
    }

    return data


__dumpshape__ = {
    om.MFn.kNurbsCurve: dumpNurbsCurve,
    om.MFn.kNurbsSurface: dumpNurbsSurface,
    om.MFn.kMesh: dumpMesh
}


def createNurbsCurve(data, scale=1.0, parent=om.MObject.kNullObj):
    """
    Creates a nurbs curve based on the supplied dictionary.

    :type data: dict
    :type scale: float
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Collect arguments
    #
    cvs = om.MPointArray([om.MPoint(x) * scale for x in data.get('controlPoints', [])])
    knots = om.MDoubleArray(data.get('knots', []))
    degree = data.get('degree', 1)
    form = data.get('form', 0)

    # Create nurbs curve using function set
    #
    fnCurve = om.MFnNurbsCurve()
    curve = fnCurve.create(cvs, knots, degree, form, False, True, parent)

    # Update line width
    #
    plug = fnCurve.findPlug('lineWidth', True)
    plug.setFloat(data.get('lineWidth', -1))

    return curve


def createNurbsCurveData(data, scale=1.0):
    """
    Creates a legacy nurbs curve data object for trim surfaces.

    :type data: dict
    :type scale: float
    :rtype: legacy.MObject
    """

    # Create new data object
    #
    fnNurbsCurveData = legacy.MFnNurbsCurveData()
    curveData = fnNurbsCurveData.create()

    # Collect control points
    #
    numControlPoints = len(data['controlPoints'])
    controlPoints = legacy.MPointArray(numControlPoints)

    for (index, controlPoint) in enumerate(data['controlPoints']):

        point = legacy.MPoint(controlPoint[0] * scale, controlPoint[1] * scale, controlPoint[2] * scale)
        controlPoints.set(point, index)

    # Collect knots
    #
    numKnots = len(data['knots'])
    knots = legacy.MDoubleArray(numKnots)

    for (index, knot) in enumerate(data['knots']):

        knots.set(knot, index)

    # Get curve parameters
    #
    degree = data.get('degree', 1)
    form = data.get('form', 0)

    fnNurbsCurve = legacy.MFnNurbsCurve()
    fnNurbsCurve.create(controlPoints, knots, degree, form, False, True, curveData)

    return curveData


def trimNurbsSurface(items, scale=1.0, surface=legacy.MObject.kNullObj):
    """
    Creates a trim surface on the supplied nurbs surface.
    Sadly this method on works with the legacy API methods...c'mon Autodesk!

    :type items: list[dict]
    :type scale: float
    :type surface: legacy.MObject
    :type: legacy.MTrimBoundaryArray
    """

    # Build curve data array
    #
    numItems = len(items)
    curveDataArray = legacy.MObjectArray(numItems)

    for (index, data) in enumerate(items):

        curveData = createNurbsCurveData(data)
        curveDataArray.set(curveData, index)

    # Append curves to trim array
    #
    boundaries = legacy.MTrimBoundaryArray()
    boundaries.append(curveDataArray)

    # Apply trim boundary to nurbs surface
    #
    fnNurbsSurface = legacy.MFnNurbsSurface(surface)
    fnNurbsSurface.trimWithBoundaries(boundaries)

    return boundaries


def createNurbsSurface(data, scale=1.0, parent=om.MObject.kNullObj):
    """
    Creates a nurbs surface based on the supplied dictionary.

    :type data: dict
    :type scale: float
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Collect arguments
    #
    cvs = om.MPointArray([om.MPoint(x[0] * scale, x[1] * scale, x[2] * scale) for x in data.get('controlPoints', [])])
    uKnots = om.MDoubleArray(data.get('uKnots', []))
    vKnots = om.MDoubleArray(data.get('vKnots', []))
    uDegree = data.get('uDegree', 1)
    vDegree = data.get('vDegree', 1)
    uForm = data.get('uForm', 0)
    vForm = data.get('vForm', 0)

    # Create nurbs surface from function set
    #
    fnNurbsSurface = om.MFnNurbsSurface()
    surface = fnNurbsSurface.create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm, True, parent)

    # Create trim surfaces
    # This can only be done with the legacy API!!!
    #
    trimNurbsSurface(data.get('boundaries', []), scale=scale, surface=dagutils.demoteMObject(surface))

    # Update curve precision
    #
    plug = fnNurbsSurface.findPlug('curvePrecisionShaded', True)
    plug.setFloat(data.get('precision', 4))

    return surface


def createMesh(data, scale=1.0, parent=om.MObject.kNullObj):
    """
    Creates a mesh based on the supplied dictionary.

    :type data: dict
    :type scale: float
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Collect arguments
    #
    vertices = om.MPointArray([om.MPoint(x) * scale for x in data.get('controlPoints', [])])
    polygonCounts = data.get('polygonCounts', [])
    polygonConnects = data.get('polygonConnects', [])

    # Create mesh from function set
    #
    fnMesh = om.MFnMesh()
    mesh = fnMesh.create(vertices, polygonCounts, list(chain(*polygonConnects)), parent=parent)

    # Set edge smoothings
    #
    edgeSmoothings = data.get('edgeSmoothings', [])

    for edgeIndex in range(fnMesh.numEdges):

        fnMesh.setEdgeSmoothing(edgeIndex, edgeSmoothings[edgeIndex])

    fnMesh.cleanupEdgeSmoothing()

    # Set face vertex normals
    #
    faceVertexNormals = data.get('faceVertexNormals', [])

    for polygonIndex in range(fnMesh.numPolygons):

        faceVertices = fnMesh.getPolygonVertices(polygonIndex)
        normals = faceVertexNormals[polygonIndex]

        for (faceVertexIndex, faceVertexNormal) in zip(faceVertices, normals):

            fnMesh.setFaceVertexNormal(om.MVector(faceVertexNormal), polygonIndex, faceVertexIndex)

    return mesh


__createshape__ = {
    om.MFn.kNurbsCurve: createNurbsCurve,
    om.MFn.kNurbsSurface: createNurbsSurface,
    om.MFn.kMesh: createMesh
}


def createShaderNetwork(side):
    """
    Creates a shader network based on the supplied side.

    :type side: int
    :rtype: list[str, str]
    """

    # Create shader
    #
    shader = mc.shadingNode(
        'surfaceShader',
        asShader=True,
        name=SURFACE_SHADERS[side]
    )

    shadingGrp = mc.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name=SHADING_ENGINES[side]
    )

    mc.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % shadingGrp)

    # Edit shader values
    #
    colour = COLOUR_RGB[side]

    mc.setAttr('%s.outColor' % shader, colour[0], colour[1], colour[2], type='double3')
    mc.setAttr('%s.outTransparency' % shader, 0.75, 0.75, 0.75, type='double3')

    return [shader, shadingGrp]


def getShaderNodes(side):
    """
    Retrieves the shader network for the given side.

    :type side: int
    :rtype: list[str, str]
    """

    # Concatenate shader name
    #
    shader = SURFACE_SHADERS[side]
    shadingGrp = SHADING_ENGINES[side]

    if mc.objExists(shadingGrp):

        return [shader, shadingGrp]

    else:

        return createShaderNetwork(side)


def applyColorIndex(shape, colorIndex):
    """
    Applies the color index to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorIndex: int
    :rtype: None
    """

    # Initialize function set
    #
    fnDependNode = om.MFnDependencyNode(shape)

    # Enable color overrides
    #
    fnDependNode.findPlug('overrideEnabled', False).setBool(True)
    fnDependNode.findPlug('overrideRGBColors', False).setBool(False)

    # Set color index
    #
    fnDependNode.findPlug('overrideColor').setInt(colorIndex)


def applyColorRGB(shape, colorRGB):
    """
    Applies the color RGB to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorRGB: list[float, float, float]
    :rtype: None
    """

    # Initialize function set
    #
    fnDependNode = om.MFnDependencyNode(shape)

    # Enable color overrides
    #
    fnDependNode.findPlug('overrideEnabled', False).setBool(True)
    fnDependNode.findPlug('overrideRGBColors', False).setBool(True)

    # Set color RGB values
    #
    fnDependNode.findPlug('overrideColorR', False).setFloat(colorRGB[0])
    fnDependNode.findPlug('overrideColorG', False).setFloat(colorRGB[0])
    fnDependNode.findPlug('overrideColorB', False).setFloat(colorRGB[0])


def applyColorSide(shape, side):
    """
    Applies the color to the supplied shape node based on the side.

    :type shape: Union[om.MObject, om.MDagPath]
    :type side: int
    :rtype: None
    """

    # Check node type
    #
    if shape.hasFn(om.MFn.kMesh) or shape.hasFn(om.MFn.kNurbsSurface):

        # Add shape to shading group
        #
        shader, shadingGrp = getShaderNodes(side)

        fullPathName = om.MDagPath.getAPathTo(shape).fullPathName()
        mc.sets(fullPathName, edit=True, forceElement=shadingGrp)

    else:

        # Assign color index
        #
        applyColorIndex(shape, COLOR_INDEX[side])


def applyLineWidth(transform, lineWidth=-1.0):

    pass


def colorizeShape(shape, **kwargs):
    """
    Colorizes the supplied shape node based on the supplied arguments.

    :rtype: None
    """

    # Check if a color index was supplied
    #
    colorIndex = kwargs.get('colorIndex', None)

    if colorIndex is not None:

        return applyColorIndex(shape, colorIndex)

    # Check if a color RGB was supplied
    #
    colorRGB = kwargs.get('colorRGB', None)

    if colorRGB is not None:

        return applyColorRGB(shape, colorRGB)

    # Check if a side was supplied
    #
    side = kwargs.get('side', None)

    if side is not None:

        return applyColorSide(shape, side)


def filterUserInput(userInput):
    """
    Removes any invalid characters from user supplied string.

    :type userInput: str
    :rtype: str
    """

    # Query string length
    #
    if len(userInput) > 0:

        return "".join([char for char in userInput if re.match(r'\w', char)])

    else:

        return "untitled"


def getUserSavePath():
    """
    Prompts the user for a save path for a json file.

    :rtype: str
    """

    # Prompt user for input
    #
    result = mc.promptDialog(
        title='Save Shape',
        message='Enter Shape Name:',
        button=['Save', 'Cancel'],
        defaultButton='Save',
        cancelButton='Cancel',
        dismissString='Cancel'
    )

    if result == 'Save':

        # Write dictionary to json file
        #
        userInput = mc.promptDialog(query=True, text=True)
        name = filterUserInput(userInput)

        directory = getShapesDirectory()
        filename = '{name}.json'.format(name=name)

        filePath = os.path.join(directory, filename)

        # Check if file exists
        #
        if os.path.exists(filePath):

            # Confirm with user
            #
            result = mc.confirmDialog(
                title='Save Shape',
                message='%s already exists.\rDo you want to replace it?' % filename,
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No'
            )

            if result == 'No':

                log.info('Operation aborted...')
                return None

        # Return save path
        #
        return filePath

    else:

        log.info('Operation aborted...')
        return None


def saveShapesFromTransform(transform, filePath=None):
    """
    Saves out the shape nodes located under the given transform.

    :type transform: om.MObject
    :type filePath: str
    :rtype: str
    """

    # Check api type
    #
    if not transform.hasFn(om.MFn.kTransform):

        log.warning('saveShape() expects a transform node (%s given)!' % transform.apiTypeStr)

    # Query shape quantity
    #
    dagPath = om.MDagPath.getAPathTo(transform)
    shapes = []

    for child in dagutils.iterShapes(dagPath):

        # Get dump method
        #
        method = __dumpshape__.get(child.apiType(), None)

        if method is None:

            log.warning('Unable to locate suitable serialize method for: %s type!' % child.apiTypeStr)
            continue

        # Dump data from shape
        #
        data = method(child)
        shapes.append(data)

    # Check how many items were dumped
    #
    if len(shapes) == 0:

        log.info('saveShape() expects a transform with valid shape nodes!')
        return

    # Check if file path is valid
    #
    savePath = filePath if filePath is not None else getUserSavePath()

    if savePath is not None:

        # Commit data to file
        #
        with open(filePath, 'w') as jsonFile:

            json.dump(shapes, jsonFile, indent=4)

        # Return save path
        #
        log.info('Saving shapes to: %s' % filePath)
        return filePath


def saveShapesFromSelection():
    """
    Saves all of the transform nodes from the active selection.

    :rtype: None
    """

    # Get active selection
    #
    selectionList = om.MGlobal.getActiveSelectionList()
    selectionCount = selectionList.length()

    for i in range(selectionCount):

        # Check if the user selected a shape
        #
        dependNode = selectionList.getDependNode(i)

        if dependNode.hasFn(om.MFn.kShape):

            dependNode = om.MFn.kDagNode(dependNode).parent(0)

        # Check if this is a transform
        #
        if dependNode.hasFn(om.MFn.kTransform):

            saveShapesFromTransform(dependNode)

        else:

            continue


def addShapeToTransform(name, **kwargs):
    """
    Recreates the shapes from the supplied name.
    This name will be used to lookup the json file from the shapes directory.

    :type name: str
    :keyword colorIndex: int
    :keyword colorRGB: list[float, float, float]
    :keyword side: int
    :keyword scale: float
    :keyword parent: om.MObject
    :rtype: list[om.MObject]
    """

    # Concatenate file path
    #
    items = loadShape(name)

    if items is None:

        return

    # Check if parent is valid
    #
    parent = kwargs.get('parent', om.MObject.kNullObj)

    if parent.isNull():

        parent = dagutils.createDagNode('transform')

    # Iterate through shape nodes
    #
    shapes = []
    scale = kwargs.get('scale', 1.0)

    for data in items:

        # Query shape type
        #
        apiType = data.get('apiType', 0)
        func = __createshape__.get(apiType, None)

        if func is None:

            log.warning('addShapeToTransform() expects a valid api type (%s given)!' % apiType)
            continue

        # Create shape node
        #
        shape = func(data, scale=scale, parent=parent)
        shapes.append(shape)

        # Colorize shape
        #
        colorizeShape(shape, **kwargs)

    # Return list of shapes
    #
    return shapes
