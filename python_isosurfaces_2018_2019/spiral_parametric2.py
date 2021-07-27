#!/usr/bin/env python3

import sys
import numpy
import stl.mesh

# TODO:
# - Fix correction around high curvatures.  It has boundary issues
# between the functions.
# - Check every vertex point against the actual isosurface.
# - Check rotation direction
# - Fix phase, which only works if 0!

fname = "spiral_inner0_one_period.stl"
freq = 20
phase = 0
scale = 1/16 # from libfive
inner = 0.4 * scale
outer = 2.0 * scale
rad = 0.3 * scale
ext_phase = 0

"""
fname = "spiral_outer90_one_period.stl"
freq = 10
#phase = numpy.pi/2
phase = 0
scale = 1/16 # from libfive
inner = 0.9 * scale
outer = 2.0 * scale
rad = 0.3 * scale
ext_phase = numpy.pi/2
"""

def angle(z):
    return freq*z + phase

def max_z():
    # This value is the largest |z| for which 'radical' >= 0
    # (thus, for x_cross to have a valid solution)
    return (numpy.arcsin(rad / inner) - phase) / freq

def radical(z):
    return rad*rad - inner*inner * (numpy.sin(angle(z)))**2

def x_cross(z, sign):
    # Single cross-section point in XZ for y=0.  Set sign for positive
    # or negative solution.
    n1 = numpy.sqrt(radical(z))
    n2 = inner * numpy.cos(angle(z))
    if sign > 0:
        return (n2-n1) / outer
    else:
        return (n2+n1) / outer

def curvature_cross(z, sign):
    # Curvature at a given cross-section point.  This is fugly because
    # it was produced from Maxima's optimized expression.
    a1 = 1/outer
    a2 = freq**2
    a3 = phase + z*freq
    a4 = numpy.cos(a3)
    a5 = a4**2
    a6 = numpy.sin(a3)
    a7 = a6**2
    a8 = inner**2
    a9 = numpy.sqrt(rad**2 - a8*a7)
    a10 = -a2*(inner**4)*a5*a7 / (a9**3)
    a11 = 1 / a9
    a12 = -a2*a8*a5*a11
    a13 = a2*a8*a7*a11
    a14 = 1/(outer**2)
    a15 = -freq*a8*a4*a6*a11
    if sign > 0:
        return -a1*(a13+a12+a10+a2*inner*a4) / ((a14*(a15+freq*inner*a6)**2 + 1)**(3/2))
    else:
        return a1*(a13+a13+a10-a2*inner*a4) / ((a14*(a15-freq*inner*a6)**2 + 1)**(3/2))

def cross_section_xz(eps):
    # Generate points for a cross-section in XZ.  'eps' is the maximum
    # distance in either axis.
    verts = []
    signs = [-1, 1]
    z_start = [0, max_z()]
    z_end = [max_z(), 0]
    # Yes, this is clunky and numerical:
    for sign, z0, z1 in zip(signs, z_start, z_end):
        print("sign={} z0={} z1={}".format(sign, z0, z1))
        z = z0
        x = x_cross(z, sign)
        while (sign*z) >= (sign*z1):
            verts.append([x, 0, z])
            x_last = x
            dz = -sign*min(eps, abs(z - z1))
            if abs(dz) < 1e-8:
                break
            x = x_cross(z + dz, sign)
            #curvature = max(abs(curvature_cross(z, sign)), abs(curvature_cross(z + dz, sign)))
            curvature = abs(curvature_cross((z + dz)/2, sign))
            dx = (x - x_last) * curvature
            print("start x={} dx={} z={} dz={} curvature={}".format(x, dx, z, dz, curvature))
            while abs(dx) > eps:
                dz *= 0.8
                x = x_cross(z + dz, sign)
                curvature = abs(curvature_cross((z + dz)/2, sign))
                #curvature = max(abs(curvature_cross(z, sign)), abs(curvature_cross(z + dz, sign)))
                dx = (x - x_last) * curvature
                print("iter x={} dx={} z={} dz={} curvature={}".format(x, dx, z, dz, curvature))
            z = z + dz
            print("finish x={} z={} curvature={}".format(x, z, curvature))
    n = len(verts)
    data = numpy.zeros((n*2, 3))
    data[:n, :] = verts
    data[n:, :] = verts[::-1]
    data[n:, 2] = -data[n:, 2]
    return data

def turn(points, dz):
    # Note one full revolution is dz = 2*pi/freq
    # How far to turn in radians (determined by dz):
    rad = angle(dz)
    c, s = numpy.cos(rad), numpy.sin(rad)
    mtx = numpy.array([
        [ c,  s,  0],
        [-s,  c,  0],
        [ 0,  0,  1],
    ])
    return points.dot(mtx) + [0, 0, dz]

def screw_360(eps, dz):
    #z0 = -10 * 2*numpy.pi/freq / 2
    z0 = -5 * 2*numpy.pi/freq / 2
    z1 = z0 + 2*numpy.pi/freq
    #z1 = 5 * 2*numpy.pi/freq / 2
    #z0 = 0
    #z1 = 2*numpy.pi/freq
    init_xsec = cross_section_xz(eps)
    num_xsec_steps = init_xsec.shape[0]
    zs = numpy.arange(z0, z1, dz)
    num_screw_steps = len(zs)
    vecs = num_xsec_steps * num_screw_steps * 2 + 2*num_xsec_steps
    print("Generating {} vertices...".format(vecs))
    data = numpy.zeros(vecs, dtype=stl.mesh.Mesh.dtype)
    v = data["vectors"]
    # First endcap:
    center = init_xsec.mean(0)
    for i in range(num_xsec_steps):
        v[i][0,:] = init_xsec[(i + 1) % num_xsec_steps,:]
        v[i][1,:] = init_xsec[i,:]
        v[i][2,:] = center
    # Body:
    verts = init_xsec
    for i,z in enumerate(zs):
        verts_last = verts
        verts = turn(init_xsec, z-z0)
        if i > 0:
            for j in range(num_xsec_steps):
                # Vertex index:
                vi = num_xsec_steps + (i-1)*num_xsec_steps*2 + j*2
                v[vi][0,:] = verts[(j + 1) % num_xsec_steps,:]
                v[vi][1,:] = verts[j,:]
                v[vi][2,:] = verts_last[j,:]
                #print("Write vertex {}".format(vi))
                v[vi+1][0,:] = verts_last[(j + 1) % num_xsec_steps,:]
                v[vi+1][1,:] = verts[(j + 1) % num_xsec_steps,:]
                v[vi+1][2,:] = verts_last[j,:]
                #print("Write vertex {} (2nd half)".format(vi+1))
    # Second endcap:
    center = verts.mean(0)
    for i in range(num_xsec_steps):
        vi = num_xsec_steps * num_screw_steps * 2 + num_xsec_steps + i
        v[vi][0,:] = center
        v[vi][1,:] = verts[i,:]
        v[vi][2,:] = verts[(i + 1) % num_xsec_steps,:]
    v[:, :, 2] += z0 + ext_phase / freq
    v[:, :, :] /= scale
    mesh = stl.mesh.Mesh(data, remove_empty_areas=False)
    print("Beginning z: {}".format(z0/scale))
    print("Ending z: {}".format(z1/scale))
    print("Period: {}".format((z1-z0)/scale))
    return mesh

#print("Writing {}...".format(fname))
#mesh = stl.mesh.Mesh(data, remove_empty_areas=False)
#mesh.save(fname)
#print("Done.")

# What's up with this?  Note the jump from z=0.0424 to z=0.037.
"""
finish x=0.13228756555322954 z=0.042403103949074046 curvature=2.451108140319032
sign=1 z0=0.042403103949074046 z1=0
__main__:75: RuntimeWarning: invalid value encountered in double_scalars
start x=0.0834189730812818 dx=nan z=0.042403103949074046 dz=-0.005 curvature=nan
finish x=0.0834189730812818 z=0.03740310394907405 curvature=nan
"""
# Is it because curvature is undefined there - thus the starting step
# size of 0.005 is fine?

m = screw_360(0.01, 0.001)
print("Writing {}...".format(fname))
m.save(fname)
