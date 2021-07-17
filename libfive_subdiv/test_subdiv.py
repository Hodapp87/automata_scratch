#!/usr/bin/env python3

# Chris Hodapp, 2021-07-17
#
# This code is: yet another attempt at producing better meshes from
# implicit surfaces / isosurfaces.  My paper notes from around the
# same time period describe some more of why and how.
#
# This depends on the Python bindings for libfive (circa revision
# 601730dc), on numpy, and on autograd from
# https://github.com/HIPS/autograd for automatic differentiation.
#
# For an implicit surface expressed in a Python function, it:
# - uses libfive to generate a mesh for this implicit surface,
# - dumps this face-vertex data (numpy arrays) to disk in a form Blender
#   can load pretty easily, (this is done only because exporting and
#   loading an STL resulted in vertex and face indices being out of sync
#   for some reason, perhaps libfive's meshing having randomness.)
# - iterates over each edge from libfive's mesh data,
# - for that edge, computes the curvature of the surface perpendicular
#   to that edge,
# - saves this curvature away in another file Blender can load.
#
# There are then some Blender routines for its Python API which load
# the mesh, load the curvatures, and then try to turn these per-edge
# curvature values to edge crease weights.  The hope was that this
# would allow subdivision to work effectively on the resultant mesh in
# sharper (higher-curvature) areas - lower crease weights should fit
# lower-curvature areas better, and higher crease weights should keep
# a sharper edge from being dulled too much by subdivision.
# 
# I tried with spiral_implicit, my same spiral isosurface function
# from 2005 June yet again, as the implicit surface, but also yet
# again, it proved a very difficult surface to work with.

# Below is some elisp so that I can use the right environment in Emacs
# and elpy:
# 
# (setq python-shell-interpreter "nix-shell" python-shell-interpreter-args " -I nixpkgs=/home/hodapp/nixpkgs -p python3Packages.libfive python3Packages.autograd python3Packages.numpy --command \"python3 -i\"")

# This is a kludge to ensure libfive's bindings can be found:
#import os, sys
#os.environ["LIBFIVE_FRAMEWORK_DIR"]="/nix/store/gcxmz71b4i6bmsb1alafr4cqdnl19dn5-libfive-unstable-e93fef9d/lib/"
#sys.path.insert(0, "/nix/store/gcxmz71b4i6bmsb1alafr4cqdnl19dn5-libfive-unstable-e93fef9d/lib/python3.8/site-packages/")

import autograd.numpy as np
from autograd import grad, elementwise_grad as egrad

from libfive.shape import shape

# The implicit surface is below.  It returns two functions that
# compute the same thing: a vectorized version (f) that can handle
# array inputs with (x,y,z) rows, and a version (g) that can also
# handle individual x,y,z. f is needed for autograd, g is needed for
# libfive.
def spiral_implicit(outer, inner, freq, phase, thresh):
    def g(x,y,z):
        d1 = outer*y - inner*np.sin(freq*x + phase)
        d2 = outer*z - inner*np.cos(freq*x + phase)
        return d1*d1 + d2*d2 - thresh*thresh
    def f(pt):
        x,y,z = [pt[..., i] for i in range(3)]
        return g(x,y,z)
    return f, g

def any_perpendicular(vecs):
    # For 'vecs' of shape (..., 3), this returns an array of shape
    # (..., 3) in which every corresponding vector is perpendicular
    # (but nonzero).  'vecs' does not need to be normalized, and the
    # returned vectors are not normalized.
    x,y,z = [vecs[..., i] for i in range(3)]
    a0 = np.zeros_like(x)
    # The condition has the extra dimension added to make it (..., 1)
    # so it broadcasts properly with the branches, which are (..., 3):
    p = np.where((np.abs(z) < np.abs(x))[...,None],
                 np.stack((y,  -x, a0), axis=-1),
                 np.stack((a0, -z, y),  axis=-1))
    return p

def intersect_implicit(surface_fn):
    # surface_fn(x,y,z)=0 is an implicit surface.  This returns a
    # function f(s, t, pt, u, v) which - for f(s,t,...) = 0 is the
    # implicit curve created by intersecting the surface with a plane
    # passing through point 'pt' and with two perpendicular unit
    # vectors 'u' and 'v' that lie on the plane.
    def g(pts_2d, pt_center, u, v, **kw):
        s,t = [pts_2d[..., i, None] for i in range(2)]
        pt_3d = pt_center + s*u + t*v
        return surface_fn(pt_3d, **kw)
    return g

def implicit_curvature_2d(curve_fn):
    # Returns a function which computes curvature of an implicit
    # curve, curve_fn(s,t)=0.  The resultant function takes two
    # arguments as well.
    #
    # First derivatives:
    _g1 = egrad(curve_fn)
    # Second derivatives:
    _g2s = egrad(lambda *a, **kw: _g1(*a, **kw)[...,0])
    _g2t = egrad(lambda *a, **kw: _g1(*a, **kw)[...,1])
    # Doing 'egrad' twice doesn't have the intended effect, so here I
    # split up the first derivative manually.
    def f(st, **kw):
        g1  = _g1(st, **kw)
        g2s = _g2s(st, **kw)
        g2t = _g2t(st, **kw)
        ds  = g1[..., 0]
        dt  = g1[..., 1]
        dss = g2s[..., 0]
        dst = g2s[..., 1]
        dtt = g2t[..., 1]
        return (-dt*dt*dss + 2*ds*dt*dst - ds*ds*dtt) / ((ds*ds + dt*dt)**(3/2))
    return f

f_arr, f = spiral_implicit(2.0, 0.4, 20.0, 0.0, 0.3)
fs = shape(f)
print(fs)

kw={
    "xyz_min": (-0.5, -0.5, -0.5),
    "xyz_max": (0.5, 0.5, 0.5),
    "resolution": 20,
}
# To save directly as STL:
# fs.save_stl("spiral.stl", **kw)

print(f"letting libfive generate mesh...")
verts, tris = fs.get_mesh(**kw)
verts = np.array(verts, dtype=np.float32)
tris = np.array(tris, dtype=np.uint32)

print(f"Saving {len(verts)} vertices, {len(tris)} faces")
np.save("spiral_verts.npy", verts)
np.save("spiral_tris.npy", tris)

print(f"Computing curvatures...")

# Shape (N, 3, 3). Final axis is (x,y,z).
tri_verts = verts[tris]
# Compute all 3 midpoints (over each edge):
v_pairs = [(tri_verts[:, i, :], tri_verts[:, (i+1)%3, :])
           for i in range(3)]
print(f"midpoints")
tri_mids = np.stack([(vi+vj)/2 for vi,vj in v_pairs],
                    axis=1)
print(f"edge vectors")
# Compute normalized edge vectors:
diff = [vj-vi for vi,vj in v_pairs]
edge_vecs = np.stack([d/np.linalg.norm(d, axis=1, keepdims=True) for d in diff],
                     axis=1)
print(f"perpendiculars")
# Find perpendicular to all edge vectors:
v1 = any_perpendicular(edge_vecs)
v1 /= np.linalg.norm(v1, axis=-1, keepdims=True)
# and perpendiculars to both:
v2 = np.cross(edge_vecs, v1)

print(f"implicit curves")
isect_2d = intersect_implicit(f_arr)
curv_fn = implicit_curvature_2d(isect_2d)
print(f"gradients & curvature")
k = curv_fn(np.zeros((tri_mids.shape[0], 3, 2)), pt_center=tri_mids, u=v1, v=v2)

print(f"writing")
np.save("spiral_curvature.npy", k)

# for i,k_i in enumerate(k):
#     for j in range(k.shape[1]):
#         mid = tri_mids[i, j, :]
#         k_ij = k[i,j]
#         v1 = tris[i][j]
#         v2 = tris[i][(j + 1) % 3]
#         print(f"{i}: {v1} to {v2}, {k_ij:.3f}")
