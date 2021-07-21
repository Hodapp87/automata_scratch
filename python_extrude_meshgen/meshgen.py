import itertools

import meshutil
import stl.mesh
import numpy
import trimesh

# Generate a frame with 'count' boundaries in the XZ plane.
# Each one rotates by 'ang' at each step.
# dx0 is center-point distance from each to the origin.
#
# This doesn't generate usable geometry on its own.
def gen_twisted_boundary(gen=None, count=4, dx0=2, ang=0.1):
    if gen is None:
        b = numpy.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 0, 1],
            [0, 0, 1],
        ], dtype=numpy.float64) - [0.5, 0, 0.5]
        gen = itertools.repeat([b])
    # Generate 'seed' transformations:
    xfs = [meshutil.Transform().translate(dx0, 0, 0).rotate([0,1,0], numpy.pi * 2 * i / count)
           for i in range(count)]
    # (we'll increment the transforms in xfs as we go)
    for bs in gen:
        xfs_new = []
        bs2 = []
        for i, xf in enumerate(xfs):
            # Generate a boundary from running transform:
            bs2 += [xf.apply_to(b) for b in bs]
            # Increment transform i:
            xf2 = xf.rotate([0,1,0], ang)
            xfs_new.append(xf2)
        xfs = xfs_new
        yield bs2

# This is to see how well it works to compose generators:
def gen_inc_y(gen, dy=0.1):
    xf = meshutil.Transform()
    for bs in gen:
        bs2 = [xf.apply_to(b) for b in bs]
        yield bs2
        xf = xf.translate(0, dy, 0)

# Wrap a boundary generator around a (sorta) torus that is along XY.
# producing a mesh.
# 'frames' sets resolution, 'rad' sets radius (the boundary's origin
# sweeps through this radius - it's not 'inner' or 'outer' radius).
#
# generator should produce lists of boundaries which are oriented
# roughly in XZ.  This will get 'frames' elements from it if
# possible.
def gen_torus_xy(gen, rad=2, frames=100):
    ang = numpy.pi*2 / frames
    xf = meshutil.Transform().translate(rad, 0, 0)
    for i,bs in enumerate(gen):
        if i >= frames:
            break
        bs2 = [xf.apply_to(b) for b in bs]
        yield bs2
        xf = xf.rotate([0,0,1], ang)

# String together boundaries from a generator.
# If count is nonzero, run only this many iterations.
def gen2mesh(gen, count=0, flip_order=False, loop=False,
             close_first = False,
             close_last = False,
             join_fn=meshutil.join_boundary_simple):
    # Get first list of boundaries:
    bs_first = next(gen)
    bs_last = bs_first
    # TODO: Begin and end with close_boundary_simple
    meshes = []
    if close_first:
        for b in bs_first:
            meshes.append(meshutil.close_boundary_simple(b))
    for i,bs_cur in enumerate(gen):
        if count > 0 and i >= count:
            break
        for j,b in enumerate(bs_cur):
            if flip_order:
                m = join_fn(b, bs_last[j])
            else:
                m = join_fn(bs_last[j], b)
            meshes.append(m)
        bs_last = bs_cur
    if loop:
        for b0,b1 in zip(bs_last, bs_first):
            if flip_order:
                m = join_fn(b1, b0)
            else:
                m = join_fn(b0, b1)
            meshes.append(m)
    if close_last:
        for b in bs_last:
            meshes.append(meshutil.close_boundary_simple(b))
    mesh = meshutil.FaceVertexMesh.concat_many(meshes)
    return mesh
