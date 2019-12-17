#!/usr/bin/env python3

import itertools

import numpy
import stl.mesh
import trimesh

import meshutil
import meshgen
import cage

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

# Rewriting the above rewrite in terms of Cage
def ram_horn3():
    center = meshutil.Transform().translate(-0.5, -0.5, 0)
    cage0 = cage.Cage.from_arrays([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ]).transform(center)
    xf0_to_1 = meshutil.Transform().translate(0, 0, 1)
    cage1 = cage0.transform(xf0_to_1)
    opening_boundary = lambda i: meshutil.Transform() \
                                         .translate(0,0,-1) \
                                         .scale(0.5) \
                                         .translate(0.25,0.25,1) \
                                         .rotate([0,0,1], i*numpy.pi/2)
    incr = meshutil.Transform() \
                   .scale(0.9) \
                   .rotate([-1,0,1], 0.3) \
                   .translate(0,0,0.8)
    def recur(xf):
        while True:
            cage2 = cage1.transform(xf)
            yield cage2
            xf = incr.compose(xf)
    # TODO: I think there is a way to express 'recur' in the form of
    # itertools.accumulate, and it might be clearer. This function is
    # just iteratively re-composing 'incr' into a seed transformation,
    # and applying this transformation (at every stage) to the same
    # mesh.
    gens = [cage.CageGen(recur(opening_boundary(i))) for i in range(4)]
    cg = cage.CageGen(itertools.chain([cage0, cage1, cage.CageFork(gens)]))
    # TODO: if this is just a list it seems silly to require itertools
    mesh = cg.to_mesh(count=128, close_first=True, close_last=True)
    return mesh

def ram_horn_branch():
    center = meshutil.Transform().translate(-0.5, -0.5, 0)
    cage0 = cage.Cage.from_arrays([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ]).transform(center)
    incr = meshutil.Transform() \
                   .scale(0.9) \
                   .rotate([-1,0,1], 0.3) \
                   .translate(0,0,0.8)
    def recur(xf, cage1, count):
        for i in range(count):
            if i > 0:
                c = cage1.transform(xf)
                #print("DEBUG: recur, i={}, yield {}".format(i, c.verts))
                yield c
            xf0 = xf
            xf = incr.compose(xf)
        # .compose(opening_boundary(i))
        def xf_sub(i):
            # yes, I can do this in a one-liner
            # yes, it should be normalized, but I reused from something else
            if i == 0:
                dx, dy = 1, 1
            elif i == 1:
                dx, dy = -1, 1
            elif i == 2:
                dx, dy = -1, -1
            elif i == 3:
                dx, dy = 1, -1
            return meshutil.Transform().translate(0, 0, 0.5).rotate([-dy,dx,0], -numpy.pi/6)
        subdiv, trans_vs, trans_es = cage1.subdivide_deprecated()
        gens = [cage.CageGen(itertools.chain(
                    [cage_sub.transform(xf)],
                    recur(xf_sub(i).compose(xf), cage_sub, 8)))
                for i,cage_sub in
                enumerate(subdiv)]
        yield cage.CageFork(gens, xf.apply_to(trans_vs), trans_es)
        # TODO: The starting cage needs to be one iteration *earlier*, and the
        # subdivided cage is fine, but the generators likewise need to start
        # one iteration earlier.  Look closely in Blender at the mesh,
        # specifically just prior to the fork.
        #
        # xf0.apply_to(trans_vs) is identical to last cage yielded?
    cg = cage.CageGen(itertools.chain(
        [cage0],
        recur(meshutil.Transform(), cage0, 8),
    ))
    # TODO: if this is just a list it seems silly to require itertools
    mesh = cg.to_mesh(count=32, close_first=True, close_last=True)
    return mesh

def branch_test():
    b0 = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
    ], dtype=numpy.float64) - [0.5, 0.5, 0]
    parts = [meshutil.Transform().scale(0.5).translate(dx, dy, 1)
             for dx in (-0.25,+0.25) for dy in (-0.25,+0.25)]
    xf = meshutil.Transform().translate(0,0,0.1).scale(0.95)
    def gen():
        b = b0
        for i in range(10):
            b = xf.apply_to(b)
            yield [b]
    return meshgen.gen2mesh(gen(), close_first=True, close_last=True)

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
    # since it needs a generator:
    gen_inner = itertools.repeat(bs)
    gen = meshgen.gen_inc_y(meshgen.gen_twisted_boundary(gen_inner))
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
    # since it needs a generator:
    gen_inner = itertools.repeat(bs)
    # In order to make this line up properly:
    angle = numpy.pi * 2 * turns / frames
    gen = meshgen.gen_torus_xy(meshgen.gen_twisted_boundary(gen=gen_inner, count=count, ang=angle), rad=rad, frames=frames)
    return meshgen.gen2mesh(gen, 0, flip_order=True, loop=True)

def spiral_nested_2():
    # Slow.
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [0, 0, 1],
    ], dtype=numpy.float64) - [0.5, 0, 0.5]
    b *= 0.3
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    bs = [b]
    # since it needs a generator:
    gen1 = itertools.repeat(bs)
    gen2 = meshgen.gen_twisted_boundary(gen1, ang=-0.2, dx0=0.5)
    gen3 = meshgen.gen_twisted_boundary(gen2, ang=0.05, dx0=1)
    gen = meshgen.gen_inc_y(gen3, dy=0.1)
    return meshgen.gen2mesh(
        gen, count=250, flip_order=True, close_first=True, close_last=True)

def spiral_nested_3():
    # Slower.
    b = numpy.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [0, 0, 1],
    ], dtype=numpy.float64) - [0.5, 0, 0.5]
    b *= 0.3
    b = meshutil.subdivide_boundary(b)
    b = meshutil.subdivide_boundary(b)
    bs = [b]
    # since it needs a generator:
    gen1 = itertools.repeat(bs)
    gen2 = meshgen.gen_twisted_boundary(gen1, ang=-0.2, dx0=0.5)
    gen3 = meshgen.gen_twisted_boundary(gen2, ang=0.07, dx0=1)
    gen4 = meshgen.gen_twisted_boundary(gen3, ang=-0.03, dx0=3)
    gen = meshgen.gen_inc_y(gen4, dy=0.1)
    return meshgen.gen2mesh(
        gen, count=500, flip_order=True, close_first=True, close_last=True)

def main():
    fns = {
        ram_horn: "ramhorn.stl",
        ram_horn2: "ramhorn2.stl",
        # TODO: Fix
        #ram_horn3: "ramhorn3.stl",
        ram_horn_branch: "ramhorn_branch.stl",
        twist: "twist.stl",
        twist_nonlinear: "twist_nonlinear.stl",
        twist_from_gen: "twist_from_gen.stl",
        twisty_torus: "twisty_torus.stl",
        spiral_nested_2: "spiral_nested_2.stl",
        spiral_nested_3: "spiral_nested_3.stl",
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
