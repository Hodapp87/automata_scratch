#!/usr/bin/env python3

import stl.mesh
import numpy
import trimesh

import meshutil
import meshgen

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
    meshes = []
    meshes.append(meshutil.join_boundary_simple(b0, b1))
    meshes.append(meshutil.close_boundary_simple(b0))
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
            meshes.append(m)
            xf = incr.compose(xf)
        # Close final boundary:
        meshes.append(meshutil.close_boundary_simple(b_sub1[::-1,:]))
        # ::-1 is to reverse the boundary's order to fix winding order.
        # Not sure of the "right" way to fix winding order here.
        # The boundary vertices go in an identical order... it's just
        # that clockwise/counter-clockwise flip.

    # I keep confusing the 'incremental' transform with the
    # transform to get b_open in the first place

    # I don't need to subdivide *geometry*.
    # I need to subdivide *space* and then put geometry in it.
    mesh = meshutil.FaceVertexMesh.concat_many(meshes)
    return mesh

# Rewriting the above in terms of generators & iterated transforms
def ram_horn_gen(b, xf):
    while True:
        b1 = xf.apply_to(b)
        yield [b1]
        incr = meshutil.Transform() \
            .scale(0.9) \
            .rotate([-1,0,1], 0.3) \
            .translate(0,0,0.8)
        xf = incr.compose(xf)

def ram_horn2():
    b0 = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=numpy.float64) - [0.5, 0.5, 0]
    xf0_to_1 = meshutil.Transform().translate(0,0,1)
    b1 = xf0_to_1.apply_to(b0)
    meshes = []
    meshes.append(meshutil.join_boundary_simple(b0, b1))
    meshes.append(meshutil.close_boundary_simple(b0))
    for i in range(4):
        # Opening boundary:
        xf = meshutil.Transform() \
            .translate(0,0,-1) \
            .scale(0.5) \
            .translate(0.25,0.25,1) \
            .rotate([0,0,1], i*numpy.pi/2)
        gen = ram_horn_gen(b1, xf)
        mesh = meshgen.gen2mesh(gen, count=128, close_last=True)
        meshes.append(mesh)
    mesh = meshutil.FaceVertexMesh.concat_many(meshes)
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
    meshes = []
    for i in range(count):
        xf = meshutil.Transform() \
            .translate(dx0, 0, 0) \
            .rotate([0,0,1], numpy.pi * 2 * i / count)
        b0 = xf.apply_to(b)
        meshes.append(meshutil.close_boundary_simple(b0))
        for layer in range(256):
            b_sub0 = xf.apply_to(b)
            incr = meshutil.Transform() \
                .rotate([0,0,1], ang) \
                .translate(0,0,dz) \
                .scale(scale)
            b_sub1 = xf.compose(incr).apply_to(b)
            m = meshutil.join_boundary_simple(b_sub0, b_sub1)
            meshes.append(m)
            xf = xf.compose(incr)
        # Close final boundary:
        meshes.append(meshutil.close_boundary_simple(b_sub1[::-1,:]))
    mesh = meshutil.FaceVertexMesh.concat_many(meshes)
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
    meshes = []
    for i in range(count):
        xf = meshutil.Transform() \
            .translate(dx0, 0, 0) \
            .rotate([0,0,1], numpy.pi * 2 * i / count)
        b0 = xf.apply_to(b)
        meshes.append(meshutil.close_boundary_simple(b0))
        for layer in range(layers):
            b_sub0 = xf.apply_to(b)
            ang = ang_fn(layer)
            incr = meshutil.Transform() \
                .rotate([0,0,1], ang) \
                .translate(0,0,dz) \
                .scale(scale)
            b_sub1 = xf.compose(incr).apply_to(b)
            m = meshutil.join_boundary_simple(b_sub0, b_sub1)
            meshes.append(m)
            xf = xf.compose(incr)
        # Close final boundary:
        meshes.append(meshutil.close_boundary_simple(b_sub1[::-1,:]))
    mesh = meshutil.FaceVertexMesh.concat_many(meshes)
    return mesh

def twist_from_gen():
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [0, 0, 1],
    ], dtype=numpy.float64) - [0.5, 0, 0.5]
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    bs = [b]
    gen = meshgen.gen_inc_y(meshgen.gen_twisted_boundary(bs))
    mesh = meshgen.gen2mesh(gen, 100, True)
    return mesh

# frames = How many step to build this from:
# turn = How many full turns to make in inner twist
# count = How many inner twists to have
def twisty_torus(frames = 200, turns = 4, count = 4, rad = 4):
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [0, 0, 1],
    ], dtype=numpy.float64) - [0.5, 0, 0.5]
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    bs = [b]
    # In order to make this line up properly:
    angle = numpy.pi * 2 * turns / frames
    gen = meshgen.gen_torus_xy(meshgen.gen_twisted_boundary(bs=bs, count=count, ang=angle), rad=rad, frames=frames)
    return meshgen.gen2mesh(gen, 0, flip_order=True, loop=True)

def main():
    fns = {
        ram_horn: "ramhorn.stl",
        ram_horn2: "ramhorn2.stl",
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
