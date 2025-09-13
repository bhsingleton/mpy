# MPy (Maya + Python)
  
A python package used to interface with MObjects inside Maya.  
Unlike pymel, mpy uses the Maya Python API 2.0 to leverage its runtime performance gains.  
This package also pulls most of its underlying logic from the [dcc](https://github.com/bhsingleton/dcc) package's Maya [utility](https://github.com/bhsingleton/dcc/tree/main/maya/libs) modules!  
  
# MPyNode (Maya + Python + Node Interface)
The `MPyNode` class uses a singleton pattern to initialize node interfaces on demand and store them for later use to speed up performance.  
On top of this, all `MFn` function sets derived from the initialized node are fully accessible!
  
For example:  
```
from mpy import mpynode

persp = mpynode.MPyNode('persp')
hashCode = persp.hashCode()
print(mpynode.MPyNode.__instances__[hashCode])
```

### User Properties:
Metadata is an important facet of tool development.  
But figuring out where to store that data can be a challenge.  
Rather than creating extra attributes, mpy uses the builtin `notes` attribute, along with a custom MELSON (MEL + JSON) serializer, for quick convenient access to a custom mutable mapping interface.  
  
For example:  
```
from mpy import mpynode

persp = mpynode.MPyNode('persp')
persp.userProperties['restMatrix'] = persp.matrix()
print(persp.userProperties['restMatrix'])
```
  
# MPyScene (Maya + Python + Scene Interface)
Rather than memorizing all of the MEL commands for interfacing with the open scene file, mpy features a convenient `MPyScene` interface.  
This interface features several convenient methods such as: `createNode`, `createShadingNode`, `createReference`, and many many more...  
On top of this, the file properties can quickly be accessed via a custom mutable mapping interface from the `properties` property.  
  
For example:  
```
from mpy import mpyscene

scene = mpyscene.MPyScene()
print(scene.properties['UUID'])
joint = scene.createNode('joint')
print(joint)
```
