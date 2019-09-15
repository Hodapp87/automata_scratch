import stl.mesh
import numpy
import quaternion

def open_cube():
    data = numpy.zeros(8, dtype=stl.mesh.Mesh.dtype)
    v = data["vectors"]
    v[0] = [[0,0,0], [1,0,0], [1,1,0]]
    v[1] = [[0,0,0], [1,1,0], [0,1,0]]
    v[2] = [[1,0,0], [1,0,1], [1,1,1]]
    v[3] = [[1,0,0], [1,1,1], [0,0,0]]
    v[4] = [[1,0,1], [0,0,1], [0,1,1]]
    v[5] = [[1,0,1], [0,1,1], [0,0,1]]
    v[6] = [[0,0,1], [0,0,0], [0,1,0]]
    v[7] = [[0,0,1], [0,1,0], [0,1,1]]
    # Winding order might be wrong.
    return data
