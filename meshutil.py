import stl.mesh
import numpy
import quaternion

def cube(open_xz=False):
    if open_xz:
        data = numpy.zeros(8, dtype=stl.mesh.Mesh.dtype)
    else:
        data = numpy.zeros(12, dtype=stl.mesh.Mesh.dtype)
    v = data["vectors"]
    v[0] = [[0,0,0], [1,1,0], [1,0,0]]
    v[1] = [[0,0,0], [0,1,0], [1,1,0]]
    v[2] = [[1,0,0], [1,1,1], [1,0,1]]
    v[3] = [[1,0,0], [1,1,0], [1,1,1]]
    v[4] = [[1,0,1], [0,1,1], [0,0,1]]
    v[5] = [[1,0,1], [1,1,1], [0,1,1]]
    v[6] = [[0,0,1], [0,1,0], [0,0,0]]
    v[7] = [[0,0,1], [0,1,1], [0,1,0]]
    if not open_xz:
        v[8]  = [[0,1,0], [1,1,1], [1,1,0]]
        v[9]  = [[0,1,0], [0,1,1], [1,1,1]]
        v[10] = [[0,0,0], [1,0,0], [1,0,1]]
        v[11] = [[0,0,0], [1,0,1], [0,0,1]]
    return data
