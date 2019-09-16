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

def cube(open_xz=False):
    if open_xz:
        data = numpy.zeros(8, dtype=stl.mesh.Mesh.dtype)
    else:
        data = numpy.zeros(12, dtype=stl.mesh.Mesh.dtype)
    v = data["vectors"]   
    v[0] = [lbf, rtf, rbf]
    v[1] = [lbf, ltf, rtf]
    v[2] = [rbf, rtb, rbb]
    v[3] = [rbf, rtf, rtb]
    v[4] = [rbb, ltb, lbb]
    v[5] = [rbb, rtb, ltb]
    v[6] = [lbb, ltf, lbf]
    v[7] = [lbb, ltb, ltf]
    if not open_xz:
        v[8]  = [ltf, rtb, rtf]
        v[9]  = [ltf, ltb, rtb]
        v[10] = [lbf, rbf, rbb]
        v[11] = [lbf, rbb, lbb]
    return data

def cube_distort(angle):
    data = numpy.zeros(8, dtype=stl.mesh.Mesh.dtype)
    v = data["vectors"]
    q = quat.rotation_quaternion(numpy.array([-1,0,1]), angle)
    ltf2 = quat.conjugate_by(ltf, q)[0,:]
    rtf2 = quat.conjugate_by(rtf, q)[0,:]
    ltb2 = quat.conjugate_by(ltb, q)[0,:]
    rtb2 = quat.conjugate_by(rtb, q)[0,:]
    # TODO: Just make these functions work right with single vectors
    v[0] = [lbf, rtf2, rbf]
    v[1] = [lbf, ltf2, rtf2]
    v[2] = [rbf, rtb2, rbb]
    v[3] = [rbf, rtf2, rtb2]
    v[4] = [rbb, ltb2, lbb]
    v[5] = [rbb, rtb2, ltb2]
    v[6] = [lbb, ltf2, lbf]
    v[7] = [lbb, ltb2, ltf2]
    return data
