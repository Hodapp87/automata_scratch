import stl.mesh
import numpy
import quaternion

import quat

# (left/right, bottom/top, back/front)
# I'm using X to the right, Y up, Z inward
# (not that it really matters except for variable names)
lbf = numpy.array([0,0,0])
rbf = numpy.array([1,0,0])
ltf = numpy.array([0,1,0])
rtf = numpy.array([1,1,0])
lbb = numpy.array([0,0,1])
rbb = numpy.array([1,0,1])
ltb = numpy.array([0,1,1])
rtb = numpy.array([1,1,1])

class FaceVertexMesh(object):
    def __init__(self, v, f):
        # v & f should both be of shape (N,3)
        self.v = v
        self.f = f
    def concat(self, other_mesh):
        v2 = numpy.concatenate([self.v, other_mesh.v])
        # Note index shift!
        f2 = numpy.concatenate([self.f, other_mesh.f + self.v.shape[0]])
        m2 = FaceVertexMesh(v2, f2)
        return m2
    def transform(self, xform):
        # Pass a Transform
        vh = numpy.hstack([self.v, numpy.ones((self.v.shape[0], 1), dtype=self.v.dtype)])
        v2 = vh.dot(xform.mtx.T)[:,0:3]
        # TODO: why transpose?
        # TODO: fix homogenous (even if I don't use it)
        return FaceVertexMesh(v2, self.f)
    def to_stl_mesh(self):
        data = numpy.zeros(self.f.shape[0], dtype=stl.mesh.Mesh.dtype)
        v = data["vectors"]
        for i, (iv0, iv1, iv2) in enumerate(self.f):
            v[i] = [self.v[iv0], self.v[iv1], self.v[iv2]]
        return stl.mesh.Mesh(data)

class Transform(object):
    def __init__(self, mtx=None):
        if mtx is None:
            self.mtx = numpy.identity(4)
        else:
            self.mtx = mtx
    def _compose(self, mtx2):
        return Transform(mtx2 @ self.mtx)
    def scale(self, *a, **kw):
        return self._compose(mtx_scale(*a, **kw))
    def translate(self, *a, **kw):
        return self._compose(mtx_translate(*a, **kw))
    def rotate(self, *a, **kw):
        return self._compose(mtx_rotate(*a, **kw))

def mtx_scale(sx, sy=None, sz=None):
    if sy is None:
        sy = sx
    if sz is None:
        sz = sx
    return numpy.array([
        [sx, 0,  0,  0],
        [0, sy,  0,  0],
        [0,  0, sz,  0],
        [0,  0,  0,  1],
    ])

def mtx_translate(x, y, z):
    return numpy.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1],
    ])

def mtx_rotate(axis, angle):
    q = quat.rotation_quaternion(axis, angle)
    return quat.quat2mat(q)

def cube(open_xz=False):
    verts = numpy.array([
        lbf, rbf, ltf, rtf,
        lbb, rbb, ltb, rtb,
    ], dtype=numpy.float64)
    if open_xz:
        faces = numpy.zeros((8,3), dtype=int)
    else:
        faces = numpy.zeros((12,3), dtype=int)
    faces[0,:] = [0, 3, 1]
    faces[1,:] = [0, 2, 3]
    faces[2,:] = [1, 7, 5]
    faces[3,:] = [1, 3, 7]
    faces[4,:] = [5, 6, 4]
    faces[5,:] = [5, 7, 6]
    faces[6,:] = [4, 2, 0]
    faces[7,:] = [4, 6, 2]
    if not open_xz:
        faces[8,:]  = [2, 7, 3]
        faces[9,:]  = [2, 6, 7]
        faces[10,:] = [0, 1, 5]
        faces[11,:] = [0, 5, 4]
        # winding order?
    return FaceVertexMesh(verts, faces)

def cube_distort(angle, open_xz=False):
    q = quat.rotation_quaternion(numpy.array([-1,0,1]), angle)
    ltf2 = quat.conjugate_by(ltf, q)[0,:]
    rtf2 = quat.conjugate_by(rtf, q)[0,:]
    ltb2 = quat.conjugate_by(ltb, q)[0,:]
    rtb2 = quat.conjugate_by(rtb, q)[0,:]
    # TODO: Just make these functions work right with single vectors
    verts = numpy.array([
        lbf, rbf, ltf2, rtf2,
        lbb, rbb, ltb2, rtb2,
    ], dtype=numpy.float64)
    if open_xz:
        faces = numpy.zeros((8,3), dtype=int)
    else:
        faces = numpy.zeros((12,3), dtype=int)
    faces[0,:] = [0, 3, 1]
    faces[1,:] = [0, 2, 3]
    faces[2,:] = [1, 7, 5]
    faces[3,:] = [1, 3, 7]
    faces[4,:] = [5, 6, 4]
    faces[5,:] = [5, 7, 6]
    faces[6,:] = [4, 2, 0]
    faces[7,:] = [4, 6, 2]
    if not open_xz:
        faces[8,:]  = [2, 7, 3]
        faces[9,:]  = [2, 6, 7]
        faces[10,:] = [0, 1, 5]
        faces[11,:] = [0, 5, 4]
        # winding order?
    return FaceVertexMesh(verts, faces)

def join_boundary_simple(bound1, bound2):
    # bound1 & bound2 are both arrays of shape (N,3), representing
    # the points of a boundary.  This joins the two boundaries by
    # simply connecting quads (made of 2 triangles) straight across.
    #
    # Winding will proceed in the direction of the first boundary.
    #`
    # Returns FaceVertexMesh.
    n = bound1.shape[0]
    vs = numpy.concatenate([bound1, bound2])
    # Indices 0...N-1 are from bound1, N...2*N-1 are from bound2
    fs = numpy.zeros((2*n, 3), dtype=int)
    for i in range(n):
        v0 = i
        v1 = (i + 1) % n
        fs[2*i]     = [n + v1, n + v0, v0]
        fs[2*i + 1] = [v1,     n + v1, v0]
    return FaceVertexMesh(vs, fs)
