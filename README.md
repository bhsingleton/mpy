# MPy (Maya + Python)
  
A python package used to interface with MObjects inside Maya using the `maya.api.OpenMaya` bindings.  
This package pulls alot of its underlying logic from the [dcc](https://github.com/bhsingleton/dcc) package's Maya [utility](https://github.com/bhsingleton/dcc/tree/main/maya/libs) modules!  
  
### How does it work?
The mpy package uses a singleton pattern to initialize interfaces on demand and store them for later use to speed up performance.  
Unlike pymel, mpy uses the Maya Python API 2.0 to leverage its runtime performance gains.  
  
All together, a basic example of mpy utilized code can look like:  
```
from mpy import mpynode

persp = mpynode.MPyNode('persp')
hashCode = persp.hashCode()
print(mpynode.MPyNode.__instances__[hashCode])
```
  
# Scene Interface
Rather than memorizing all of the MEL commands for interfacing with the open scene file, mpy features a convenient `MPyScene` interface.  
This interface features methods such as: `createNode`, `createShadingNode`, `createReference`, and many more...  
On top of this, the file properties can quickly be accessed via the `properties` property via a mutable mapping interface.  
  
For example:  
```
from mpy import mpyscene

scene = mpyscene.MPyScene()
print(scene.properties['UUID'])
joint = scene.createNode('joint')
print(joint)
```
  
# User Properties
Metadata is an important facet of tool development.  
But figuring out where to store that data can be a challenge.  
Rather than creating extra attributes, mpy uses the builtin `notes` attribute, along with a custom MELSON (MEL + JSON) serializer, for quick convenient access to a mutable mapping interface.  
  
For example:  
```
from mpy import mpynode

persp = mpynode.MPyNode('persp')
persp.userProperties['restMatrix'] = persp.matrix()
print(persp.userProperties['restMatrix'])
```
