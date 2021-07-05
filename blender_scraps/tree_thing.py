# Hasty conversion from the Rust in prosha/src/examples.rs & Barbs

# This is mostly right, except:
# - Something near the transition is wrong.
# - It doesn't yet do creases.

import numpy as np
import xform

# Mnemonics:
X = np.array([1.0, 0.0, 0.0])
Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])

class TreeThing(object):
    def __init__(self, f: float=0.6, depth: int=10, scale_min: float=0.02):
        self.scale_min = scale_min
        v = np.array([-1.0, 0.0, 1.0])
        v /= np.linalg.norm(v)
        self.incr = (xform.Transform().
                     translate(0, 0, 0.9*f).
                     rotate(v, 0.4*f).
                     scale(1.0 - (1.0 - 0.95)*f))
        # 'Base' vertices, used throughout:
        self.base = np.array([
            [-0.5, -0.5, 0.0],
            [-0.5,  0.5, 0.0],
            [ 0.5,  0.5, 0.0],
            [ 0.5, -0.5, 0.0],
        ])
        # 'Transition' vertices:
        self.trans = np.array([
            # Top edge midpoints:
            [-0.5,  0.0, 0.0],  # 0 - connects b0-b1
            [ 0.5,  0.0, 0.0],  # 2 - connects b2-b3
            [ 0.0,  0.5, 0.0],  # 1 - connects b1-b2
            [ 0.0, -0.5, 0.0],  # 3 - connects b3-b0
            # Top middle:
            [ 0.0,  0.0, 0.0],  # 4 - midpoint/centroid of all
        ])
        # splits[i] gives transformation from a 'base' layer to the
        # i'th split (0 to 3):
        self.splits = [
            xform.Transform().
            rotate(Z, np.pi/2 * i).
            translate(0.25, 0.25, 0.0).
            scale(0.5)
            for i in range(4)
        ]
        # Face & vertex accumulators:
        self.faces = []
        # self.faces will be a list of tuples (each one of length 4
        # and containing indices into self.verts)
        self.verts = []
        # self.verts will be a list of np.array of shape (3,) but will
        # be converted last-minute to tuples. (Why: we need to refer
        # to prior vertices and arithmetic is much easier from an
        # array, but Blender eventually needs tuples.)
        self.creases_side = set()
        self.creases_joint = set()
        self.depth = depth

    def run(self):
        self.verts.extend(self.base)
        self.faces.append((0, 1, 2, 3))
        self.child(xform.Transform(), self.depth, [0, 1, 2, 3])
        verts = [tuple(v) for v in self.verts]
        faces = [tuple(f) for f in self.faces]
        return verts, faces

    def trunk(self, xf: xform.Transform, b):

        if self.limit_check(xf):
            # Note opposite winding order
            verts = [b[i] for i in [3,2,1,0]]
            self.faces.append(verts)
            return

        incr = (xform.Transform().
                translate(0.0, 0.0, 1.0).
                rotate(Z, 0.15).
                rotate(X, 0.1).
                scale(0.95))
        sides = [
            xform.Transform().
            rotate(Z, -np.pi/2 * i).
            rotate(Y, -np.pi/2).
            translate(0.5, 0.0, 0.5)
            for i in range(4)
        ]
        xf2 = xf.compose(incr)
        g = xf2.apply_to(self.base)
        a0 = len(self.verts)
        self.verts.extend(g)

        # TODO: Turn this to a cleaner loop?
        self.main(iters - 1, xf2, [a0, a0 + 1, a0 + 2, a0 + 3])
        self.child(iters - 1, xf.compose(self.sides[0]),
                   [b[0], b[1], a0 + 1, a0 + 0])
        self.child(iters - 1, xf.compose(self.sides[1]),
                   [b[1], b[2], a0 + 2, a0 + 1])
        self.child(iters - 1, xf.compose(self.sides[2]),
                   [b[2], b[3], a0 + 3, a0 + 2])
        self.child(iters - 1, xf.compose(self.sides[3]),
                   [b[3], b[0], a0 + 0, a0 + 3])

    def limit_check(self, xf: xform.Transform) -> bool:
        # Assume all scales are the same (for now)
        sx,_,_ = xf.get_scale()
        return sx < self.scale_min

    def child(self, xf: xform.Transform, depth, b):
        if self.limit_check(xf):
            # Note opposite winding order
            verts = [b[i] for i in [3,2,1,0]]
            self.faces.append(verts)
            return

        if depth > 0:
            # Just recurse on the current path:
            xf2 = xf.compose(self.incr)
            n0 = len(self.verts)
            self.verts.extend(xf2.apply_to(self.base))

            # Connect parallel faces:
            n = len(self.base)
            for i, b0 in enumerate(b):
                j = (i + 1) % n
                b1 = b[j]
                a0 = n0 + i
                a1 = n0 + j
                self.faces.append((a0, a1, b1, b0))

            self.child(xf2, depth - 1, [n0, n0 + 1, n0 + 2, n0 + 3]);
        else:
            n = len(self.verts)
            self.verts.extend(xf.apply_to(self.base))
            m01 = len(self.verts)
            self.verts.extend(xf.apply_to(self.trans))
            m12, m23, m30, c = m01 + 1, m01 + 2, m01 + 3, m01 + 4
            self.faces.extend([
                # two faces straddling edge from vertex 0:
                (b[0], n+0, m01),
                (b[0], m30, n+0),
                # two faces straddling edge from vertex 1:
                (b[1], n+1, m12),
                (b[1], m01, n+1),
                # two faces straddling edge from vertex 2:
                (b[2], n+2, m23),
                (b[2], m12, n+2),
                # two faces straddling edge from vertex 3:
                (b[3], n+3, m30),
                (b[3], m23, n+3),
                # four faces from edge (0,1), (1,2), (2,3), (3,0):
                (b[0], m01, b[1]),
                (b[1], m12, b[2]),
                (b[2], m23, b[3]),
                (b[3], m30, b[0]),
            ])

            self.child(xf.compose(self.splits[0]), self.depth, [c, m12, n+2, m23]);
            self.child(xf.compose(self.splits[1]), self.depth, [c, m01, n+1, m12]);
            self.child(xf.compose(self.splits[2]), self.depth, [c, m30, n+0, m01]);
            self.child(xf.compose(self.splits[3]), self.depth, [c, m23, n+3, m30]);
