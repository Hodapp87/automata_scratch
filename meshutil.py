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
        # v & f should both be of shape (N,3)ll
        self.v = v
        self.f = f
    def concat(self, other_mesh):
        v2 = numpy.concatenate([self.v, other_mesh.v])
        # Note index shift!
        f2 = numpy.concatenate([self.f, other_mesh.f + self.v.shape[0]])
        m2 = FaceVertexMesh(v2, f2)
        return m2
    def to_stl_mesh(self):
        data = numpy.zeros(self.f.shape[0], dtype=stl.mesh.Mesh.dtype)
        v = data["vectors"]
        for i, (iv0, iv1, iv2) in enumerate(self.f):
            v[i] = [self.v[iv0], self.v[iv1], self.v[iv2]]
        return stl.mesh.Mesh(data)

def cube(open_xz=False):
    verts = numpy.array([
        lbf, rbf, ltf, rtf,
        lbb, rbb, ltb, rtb,
    ], dtype=numpy.float32)
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

def cube_distort(angle):
    q = quat.rotation_quaternion(numpy.array([-1,0,1]), angle)
    ltf2 = quat.conjugate_by(ltf, q)[0,:]
    rtf2 = quat.conjugate_by(rtf, q)[0,:]
    ltb2 = quat.conjugate_by(ltb, q)[0,:]
    rtb2 = quat.conjugate_by(rtb, q)[0,:]
    # TODO: Just make these functions work right with single vectors
    verts = numpy.array([
        lbf, rbf, ltf2, rtf2,
        lbb, rbb, ltb2, rtb2,
    ], dtype=numpy.float32)
    if True: #open_xz:
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
    if False: # not open_xz:
        faces[8,:]  = [2, 7, 3]
        faces[9,:]  = [2, 6, 7]
        faces[10,:] = [0, 1, 5]
        faces[11,:] = [0, 5, 4]
        # winding order?
    return FaceVertexMesh(verts, faces)
