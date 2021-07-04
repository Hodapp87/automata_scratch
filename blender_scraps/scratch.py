# This is a pile of patterns and snippets I've used in Blender in the
# past; it isn't meant to be run on its own.

import bmesh
import bpy

# Here is a good starting place (re: creating geometry):
# https://docs.blender.org/api/current/info_gotcha.html#n-gons-and-tessellation

# https://wiki.blender.org/wiki/Source/Modeling/BMesh/Design

# Current object's data (must be selected):
me = bpy.context.object.data

def bmesh_set_creases(obj, vert_pairs, crease_val):
    # Walk through the edges in 'obj'. For those *undirected* edges in
    # 'vert_pairs' (a set of (vi, vj) tuples, where vi and vj are vertex
    # indices, and tuple order is irrelevant), set the crease to 'crease_val'.
    bm = bmesh.new()
    bm.from_mesh(obj)
    creaseLayer = bm.edges.layers.crease.verify()
    for e in bm.edges:
        idxs = tuple([v.index for v in e.verts])
        print(idxs)
        if idxs in vert_pairs or idxs[::-1] in vert_pairs:
            e[creaseLayer] = crease_val
    bm.to_mesh(obj)
    bm.free()

# My bpy.types.MeshPolygon objects:
for i,poly in enumerate(me.polygons):
    t = type(poly)
    #print(f"poly {i}: {t}")
    verts = list(poly.vertices)
    print(f"poly {poly.index}: vertices={verts}")
    #s = poly.loop_start
    #n = poly.loop_total
    #print(f"  loop_start={s} loop_total={n}")
    #v = [l.vertex_index for l in me.loops[s:(s+n)]]
    #print(f"  loop: {v}")
    # Vector type:
    v2 = [me.vertices[i].co for i in verts]
    print(f"  verts: {v2}")
    # Yes, this works:
    #for i in verts:
    #    me.vertices[i].co.x -= 1.0

# Pattern for loading external module from Blender's Python (and
# reloading as necessary):
import sys
ext_path = "/home/hodapp/source/automata_scratch/blender_scraps"
if ext_path not in sys.path:
    sys.path.append(ext_path)
import whatever
whatever = importlib.reload(whatever)
# Note that if 'whatever' itself imports modules that may have changed
# since the last import, you may need to do this same importlib
# incantation!

# Crease access - but the wrong way to change them:
for edge in me.edges:
    v = list(edge.vertices)
    print(f"edge {edge.index}: crease={edge.crease} vertices={v}")
    #edge.crease = 0.7

# Creating a mesh with vertices & faces in Python via bpy with:
# v - list of (x, y, z) tuples
# f - list of (v0, v1, v2...) tuples, each with face's vertex indices
mesh = bpy.data.meshes.new('mesh_thing')
mesh.from_pydata(v, [], f)
mesh.update(calc_edges=True)
# set creases beforehand:
#bmesh_set_creases(mesh, b.creases_joint, 0.7)
obj = bpy.data.objects.new('obj_thing', mesh)
# set obj's transform matrix:
#obj.matrix_world = Matrix(...)
# also acceptable to set creases:
#bmesh_set_creases(obj.data, b.creases_joint, 0.7)
bpy.context.scene.collection.objects.link(obj)
