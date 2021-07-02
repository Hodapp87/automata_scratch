# Meant to be used with Blender's Python API
import sys
import importlib
import bpy

ext_path = "/home/hodapp/source/automata_scratch/blender_scraps"
if ext_path not in sys.path:
    sys.path.append(ext_path)

import menger_cube_ish
menger_cube_ish = importlib.reload(menger_cube_ish)

v,f = menger_cube_ish.cube_iterate(4)

mesh = bpy.data.meshes.new('mesh_thing')
mesh.from_pydata(v, [], f)
mesh.update(calc_edges=True)
for edge in mesh.edges:
    v = list(edge.vertices)
    edge.crease = 0.9

obj = bpy.data.objects.new('obj_thing', mesh)
bpy.context.scene.collection.objects.link(obj)
