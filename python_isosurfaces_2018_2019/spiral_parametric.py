#!/usr/bin/env python3

import sys
import numpy
import stl.mesh

# TODO:
# - This is a very naive triangulation strategy.  It needs fixing - the
# way it handles 'flatter' areas isn't optimal at all, even if the
# sharper areas are much better than from CGAL or libfive.
# - Generate just part of the mesh and then copy.  It is rotationally
# symmetric, as well as translationally symmetric at its period.

fname = "spiral_outer0.stl"
freq = 20
phase = 0
scale = 1/16 # from libfive
inner = 0.4 * scale
outer = 2.0 * scale
rad = 0.3 * scale

angle = lambda z: freq*z + phase

# z starting & ending point:
z0 = -20*scale
z1 = 20*scale
# Number of z divisions:
m = 1600
# Number of circle points:
n = 1000

dz = (z1 - z0) / (m-1)

data = numpy.zeros((m-1)*n*2 + 2*n, dtype=stl.mesh.Mesh.dtype)
# Vertex count:
# From z0 to z0+dz is n circle points joined with 2 triangles to next -> n*2
# z0+dz to z0+dz*2 is likewise... up through (m-1) of these -> (m-1)*n*2
# Two endcaps each have circle points & center point -> 2*n
# Thus: (m-1)*n*2 + 2*n
v = data["vectors"]
print("Vertex count: {}".format(m*n*2 + 2*n))

verts = numpy.zeros((n, 3), dtype=numpy.float32)

# For every z cross-section...
for z_idx in range(m):
    #sys.stdout.write(".")
    # z value:
    z = z0 + dz*z_idx
    # Angle of center point of circle (radians):
    # (we don't actually need to normalize this)
    rad = angle(z)
    c,s = numpy.cos(rad), numpy.sin(rad)
    # Center point of circle:
    cx, cy = (inner + outer)*numpy.cos(rad), (inner + outer)*numpy.sin(rad)
    # For every division of the circular cross-section...
    if z_idx == 0:
        # Begin with z0 endcap as a special case:
        verts_last = numpy.zeros((n, 3), dtype=numpy.float32)
        verts_last[:, 0] = cx
        verts_last[:, 1] = cy
        verts_last[:, 2] = z
    else:
        verts_last = verts
    verts = numpy.zeros((n, 3), dtype=numpy.float32)
    for ang_idx in range(n):
        # Step around starting angle (the 'far' intersection of the
        # line at angle 'rad' and this circle):
        rad2 = rad + 2*ang_idx*numpy.pi/n
        # ...and generate points on the circle:
        xi = cx + outer*numpy.cos(rad2)
        yi = cy + outer*numpy.sin(rad2)
        verts[ang_idx, :] = [xi, yi, z]
        #print("i={}, z={}, rad={}, cx={}, cy={}, rad2={}, xi={}, yi={}".format(i,z,rad,cx,cy, rad2, xi, yi))
    if z_idx == 0:
        for i in range(n):
            v[i][0,:] = verts[(i + 1) % n,:]
            v[i][1,:] = verts[i,:]
            v[i][2,:] = verts_last[i,:]
            #print("Write vertex {}".format(i))
    else:
        for i in range(n):
            # Vertex index:
            vi = z_idx*n*2 + i*2 - n
            v[vi][0,:] = verts[(i + 1) % n,:]
            v[vi][1,:] = verts[i,:]
            v[vi][2,:] = verts_last[i,:]
            #print("Write vertex {}".format(vi))
            v[vi+1][0,:] = verts_last[(i + 1) % n,:]
            v[vi+1][1,:] = verts[(i + 1) % n,:]
            v[vi+1][2,:] = verts_last[i,:]
            #print("Write vertex {} (2nd half)".format(vi+1))

# then handle z1 endcap:
for i in range(n):
    # See vi definition above.  z_idx ends at m-1, i ends at n-1, and
    # so evaluate vi+1 (final index it wrote), add 1 for the next, and
    # then use 'i' to step one at a time:
    vi = (m-1)*n*2 + (n-1)*2 - n + 2 + i
    v[vi][0,:] = verts[i,:]
    v[vi][1,:] = verts[(i + 1) % n,:]
    v[vi][2,:] = [cx, cy, z]
    # Note winding order (1 & 2 flipped from other endcap)
    #print("Write vertex {} (endcap)".format(vi))

print("Writing {}...".format(fname))
mesh = stl.mesh.Mesh(data, remove_empty_areas=False)
mesh.save(fname)
print("Done.")
