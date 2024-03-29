import numpy
import quaternion

def conjugate_by(vec, quat):
    """Turn 'vec' to a quaternion, conjugate it by 'quat', and return it."""
    q2 = quat * vec2quat(vec) * quat.conjugate()
    return quaternion.as_float_array(q2)[:,1:]

def rotation_quaternion(axis, angle):
    """Returns a quaternion for rotating by some axis and angle.
    
    Inputs:
    axis -- numpy array of shape (3,), with axis to rotate around
    angle -- angle in radians by which to rotate
    """
    qc = numpy.cos(angle / 2)
    qs = numpy.sin(angle / 2)
    qv = qs * numpy.array(axis)
    return numpy.quaternion(qc, qv[0], qv[1], qv[2])

def vec2quat(vs):
    qs = numpy.zeros(vs.shape[0], dtype=numpy.quaternion)
    quaternion.as_float_array(qs)[:,1:4] = vs
    return qs

def quat2mat(q):
    s = 1
    return numpy.array([
        [1-2*s*(q.y**2+q.z**2), 2*s*(q.x*q.y-q.z*q.w), 2*s*(q.x*q.z+q.y*q.w), 0],
        [2*s*(q.x*q.y+q.z*q.w), 1-2*s*(q.x**2+q.z**2), 2*s*(q.y*q.z-q.x*q.w), 0],
        [2*s*(q.x*q.z-q.y*q.w), 2*s*(q.y*q.z+q.x*q.w), 1-2*s*(q.x**2+q.y**2), 0],
        [0, 0, 0, 1],
    ])
