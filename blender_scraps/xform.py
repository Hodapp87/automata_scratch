import numpy as np

def quat2mat(qw, qx, qy, qz):
    s = 1
    return np.array([
        [1-2*s*(qy**2+qz**2), 2*s*(qx*qy-qz*qw), 2*s*(qx*qz+qy*qw), 0],
        [2*s*(qx*qy+qz*qw), 1-2*s*(qx**2+qz**2), 2*s*(qy*qz-qx*qw), 0],
        [2*s*(qx*qz-qy*qw), 2*s*(qy*qz+qx*qw), 1-2*s*(qx**2+qy**2), 0],
        [0, 0, 0, 1],
    ])

def rotation_quaternion(axis, angle):
    """Returns a quaternion for rotating by some axis and angle.
    
    Inputs:
    axis -- numpy array of shape (3,), with axis to rotate around
    angle -- angle in radians by which to rotate
    """
    qc = np.cos(angle / 2)
    qs = np.sin(angle / 2)
    qv = qs * np.array(axis)
    return (qc, qv[0], qv[1], qv[2])

class Transform(object):
    def __init__(self, mtx=None):
        if mtx is None:
            self.mtx = np.identity(4)
        else:
            self.mtx = mtx
    def _compose(self, mtx2):
        # Note pre-multiply. Earlier transforms are done first.
        return Transform(mtx2 @ self.mtx)
    def compose(self, xform):
        return self._compose(xform.mtx)
    def scale(self, *a, **kw):
        return self._compose(mtx_scale(*a, **kw))
    def translate(self, *a, **kw):
        return self._compose(mtx_translate(*a, **kw))
    def rotate(self, *a, **kw):
        return self._compose(mtx_rotate(*a, **kw))
    def reflect(self, *a, **kw):
        return self._compose(mtx_reflect(*a, **kw))
    def identity(self, *a, **kw):
        return self._compose(mtx_identity(*a, **kw))
    def apply_to(self, vs):
        # Homogeneous coords, so append a column of ones. vh is then shape (N,4):
        vh = np.hstack([vs, np.ones((vs.shape[0], 1), dtype=vs.dtype)])
        # As we have row vectors, we're doing basically (A*x)^T=(x^T)*(A^T)
        # hence transposing the matrix, while vectors are already transposed.
        return (vh @ self.mtx.T)[:,0:3]
    def get_scale(self):
        norms = np.linalg.norm(self.mtx, axis=0)
        return norms[:3]

def mtx_scale(sx, sy=None, sz=None):
    if sy is None:
        sy = sx
    if sz is None:
        sz = sx
    return np.array([
        [sx, 0,  0,  0],
        [0, sy,  0,  0],
        [0,  0, sz,  0],
        [0,  0,  0,  1],
    ])

def mtx_translate(x, y, z):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1],
    ])

def mtx_rotate(axis, angle):
    q = rotation_quaternion(axis, angle)
    return quat2mat(*q)

def mtx_reflect(axis):
    # axis must be norm-1
    axis = np.array(axis)
    axis = axis / np.linalg.norm(axis)
    a,b,c = axis[0], axis[1], axis[2]
    return np.array([
        [1-2*a*a, -2*a*b,   -2*a*c,  0],
        [-2*a*b,  1-2*b*b,  -2*b*c,  0],
        [-2*a*c,  -2*b*c,   1-2*c*c, 0],
        [0, 0, 0, 1],
    ])

def mtx_identity():
    return np.eye(4)
