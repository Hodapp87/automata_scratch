#!/usr/bin/env python3

import meshutil
import stl.mesh
import numpy
import trimesh

# I should be moving some of these things out into more of a
# standard library than an 'examples' script

# The first "working" example I had of the recursive 3D geometry
# that actually kept the manifold throughout:
def ram_horn():
    b0 = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=numpy.float64) - [0.5, 0.5, 0]
    xf0_to_1 = meshutil.Transform().translate(0,0,1)
    b1 = xf0_to_1.apply_to(b0)
    mesh = meshutil.join_boundary_simple(b0, b1)
    mesh = mesh.concat(meshutil.close_boundary_simple(b0))
    for i in range(4):
        # Opening boundary:
        b = b1
        xf = meshutil.Transform() \
            .translate(0,0,-1) \
            .scale(0.5) \
            .translate(0.25,0.25,1) \
            .rotate([0,0,1], i*numpy.pi/2)
        for layer in range(128):
            b_sub0 = xf.apply_to(b)
            incr = meshutil.Transform() \
                .scale(0.9) \
                .rotate([-1,0,1], 0.3) \
                .translate(0,0,0.8)
            b_sub1 = incr.compose(xf).apply_to(b)
            m = meshutil.join_boundary_simple(b_sub0, b_sub1)
            mesh = mesh.concat(m)
            xf = incr.compose(xf)
        # Close final boundary:
        mesh = mesh.concat(meshutil.close_boundary_simple(b_sub1[::-1,:]))
        # ::-1 is to reverse the boundary's order to fix winding order.
        # Not sure of the "right" way to fix winding order here.
        # The boundary vertices go in an identical order... it's just
        # that clockwise/counter-clockwise flip.

    # I keep confusing the 'incremental' transform with the
    # transform to get b_open in the first place

    # I don't need to subdivide *geometry*.
    # I need to subdivide *space* and then put geometry in it.
    return mesh

# Interlocking twists.
# ang/dz control resolution. dx0 controls radius. count controls
# how many twists. scale controls speed they shrink at.
def twist(ang=0.1, dz=0.2, dx0=2, count=4, scale=0.98):
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=numpy.float64) - [0.5, 0.5, 0]
    mesh = None
    for i in range(count):
        xf = meshutil.Transform() \
            .translate(dx0, 0, 0) \
            .rotate([0,0,1], numpy.pi * 2 * i / count)
        b0 = xf.apply_to(b)
        m = meshutil.close_boundary_simple(b0)
        if mesh is None:
            mesh = m
        else:
            mesh = mesh.concat(m)
        for layer in range(256):
            b_sub0 = xf.apply_to(b)
            incr = meshutil.Transform() \
                .rotate([0,0,1], ang) \
                .translate(0,0,dz) \
                .scale(scale)
            b_sub1 = xf.compose(incr).apply_to(b)
            m = meshutil.join_boundary_simple(b_sub0, b_sub1)
            mesh = mesh.concat(m)
            xf = xf.compose(incr)
        # Close final boundary:
        mesh = mesh.concat(meshutil.close_boundary_simple(b_sub1[::-1,:]))
    return mesh

def twist_nonlinear(dx0 = 2, dz=0.2, count=3, scale=0.99, layers=100):
    # This can be a function rather than a constant:
    angs = numpy.power(numpy.linspace(0.4, 2.0, layers), 2.0) / 10.0
    ang_fn = lambda i: angs[i]
    # (could it also be a function of space rather than which layer?)

    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=numpy.float64) - [0.5, 0.5, 0]
    mesh = None
    for i in range(count):
        xf = meshutil.Transform() \
            .translate(dx0, 0, 0) \
            .rotate([0,0,1], numpy.pi * 2 * i / count)
        b0 = xf.apply_to(b)
        m = meshutil.close_boundary_simple(b0)
        if mesh is None:
            mesh = m
        else:
            mesh = mesh.concat(m)
        for layer in range(layers):
            b_sub0 = xf.apply_to(b)
            ang = ang_fn(layer)
            incr = meshutil.Transform() \
                .rotate([0,0,1], ang) \
                .translate(0,0,dz) \
                .scale(scale)
            b_sub1 = xf.compose(incr).apply_to(b)
            m = meshutil.join_boundary_simple(b_sub0, b_sub1)
            mesh = mesh.concat(m)
            xf = xf.compose(incr)
        # Close final boundary:
        mesh = mesh.concat(meshutil.close_boundary_simple(b_sub1[::-1,:]))
    return mesh

# Generate a frame with 'count' boundaries in the XZ plane.
# Each one rotates by 'ang' as it moves by 'dz'.
# dx0 is center-point distance from each to the origin.
def gen_twisted_boundary(count=4, dx0=2, dz=0.2, ang=0.1):
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [0, 0, 1],
    ], dtype=numpy.float64) - [0.5, 0, 0.5]
    # Generate 'seed' transformations:
    xfs = [meshutil.Transform().translate(dx0, 0, 0).rotate([0,1,0], numpy.pi * 2 * i / count)
           for i in range(count)]
    # (we'll increment the transforms in xfs as we go)
    while True:
        xfs_new = []
        bs = []
        for i, xf in enumerate(xfs):
            # Generate a boundary from running transform:
            b_i = xf.apply_to(b)
            bs.append(b_i)
            # Increment transform i:
            xf2 = xf.rotate([0,1,0], ang)
            xfs_new.append(xf2)
        xfs = xfs_new
        yield bs

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
def gen2mesh(gen, count=0, flip_order=False, loop=False):
    # Get first list of boundaries:
    bs_first = next(gen)
    bs_last = bs_first
    # TODO: Begin and end with close_boundary_simple
    mesh = meshutil.FaceVertexMesh.Empty()
    for i,bs_cur in enumerate(gen):
        if count > 0 and i >= count:
            break
        for j,b in enumerate(bs_cur):
            if flip_order:
                m = meshutil.join_boundary_simple(b, bs_last[j])
            else:
                m = meshutil.join_boundary_simple(bs_last[j], b)
            mesh = mesh.concat(m)
        bs_last = bs_cur
    if loop:
        for b0,b1 in zip(bs_last, bs_first):
            if flip_order:
                m = meshutil.join_boundary_simple(b1, b0)
            else:
                m = meshutil.join_boundary_simple(b0, b1)
            mesh = mesh.concat(m)
    return mesh

def twist_from_gen():
    gen = gen_inc_y(gen_twisted_boundary())
    mesh = gen2mesh(gen, 100, True)
    return mesh

# frames = How many step to build this from:
# turn = How many full turns to make in inner twist
# count = How many inner twists to have
def twisty_torus(frames = 200, turns = 4, count = 4, rad = 4):
    # In order to make this line up properly:
    angle = numpy.pi * 2 * turns / frames
    gen = gen_torus_xy(gen_twisted_boundary(count=count, ang=angle), rad=rad, frames=frames)
    return gen2mesh(gen, 0, flip_order=True, loop=True)

def main():
    fns = {
        ram_horn: "ramhorn.stl",
        twist: "twist.stl",
        twist_nonlinear: "twist_nonlinear.stl",
        twist_from_gen: "twist_from_gen.stl",
        twisty_torus: "twisty_torus.stl",
    }
    for f in fns:
        fname = fns[f]
        print("Generate {}...".format(fname))
        mesh = f()
        nv = mesh.v.shape[0]
        nf = mesh.f.shape[0]
        print("Saving {} verts & {} faces...".format(nv, nf))
        mesh.to_stl_mesh().save(fname)
        print("Done.")

if __name__ == "__main__":
    main()
