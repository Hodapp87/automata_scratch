# Hasty conversion from the Rust in prosha/src/examples.rs & Barbs

import numpy as np

import xform

# Mnemonics:
X = np.array([1.0, 0.0, 0.0])
Y = np.array([0.0, 1.0, 0.0])
Z = np.array([0.0, 0.0, 1.0])

class Barbs(object):
    def __init__(self, scale_min=0.02):
        self.scale_min = scale_min
        # Incremental transform from each stage to the next:
        self.base_incr = (xform.Transform().
                          translate(0, 0, 1).
                          rotate(Z, 0.15).
                          rotate(X, 0.1).
                          scale(0.95))
        self.barb_incr = (xform.Transform().
                          translate(0, 0, 0.5).
                          rotate(Y, -0.2).
                          scale(0.8))
        # 'Base' vertices, used throughout:
        self.base = np.array([
            [-0.5, -0.5, 0.0],
            [-0.5,  0.5, 0.0],
            [ 0.5,  0.5, 0.0],
            [ 0.5, -0.5, 0.0],
        ])
        # self.sides[i] gives transformation from a 'base' layer to
        # the i'th side (0 to 3):
        self.sides = [
            xform.Transform().
            rotate(Z, -i * np.pi/2).
            rotate(Y, -np.pi/2).
            translate(0.5, 0.0, 0.5)
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

    def run(self, iters) -> (list, list):
        # 'iters' is ignored for now
        # 
        # Make seed vertices, use them for 'bottom' face, and recurse:
        self.verts.extend(self.base)
        self.faces.append((0, 1, 2, 3))
        self.main(iters, xform.Transform(), [0,1,2,3])
        verts = [tuple(v) for v in self.verts]
        faces = [tuple(f) for f in self.faces]
        return verts, faces

    def limit_check(self, xform: xform.Transform, iters) -> bool:
        # Assume all scales are the same (for now)
        sx,_,_ = xform.get_scale()
        return sx < self.scale_min

    def main(self, iters, xform, bound):

        if self.limit_check(xform, iters):
            # Note opposite winding order
            verts = [bound[i] for i in [3,2,1,0]]
            self.faces.append(verts)
            return

        xform2 = xform.compose(self.base_incr)
        g = xform2.apply_to(self.base)
        a0 = len(self.verts)
        self.verts.extend(g)

        # TODO: Turn this to a cleaner loop?
        self.main(iters - 1, xform2, [a0, a0 + 1, a0 + 2, a0 + 3])
        self.barb(iters - 1, xform.compose(self.sides[0]),
                  [bound[0], bound[1], a0 + 1, a0 + 0])
        self.barb(iters - 1, xform.compose(self.sides[1]),
                  [bound[1], bound[2], a0 + 2, a0 + 1])
        self.barb(iters - 1, xform.compose(self.sides[2]),
                  [bound[2], bound[3], a0 + 3, a0 + 2])
        self.barb(iters - 1, xform.compose(self.sides[3]),
                  [bound[3], bound[0], a0 + 0, a0 + 3])

    def barb(self, iters, xform, bound):
        if self.limit_check(xform, iters):
            # Note opposite winding order
            verts = [bound[i] for i in [3,2,1,0]]
            self.faces.append(verts)
            return

        xform2 = xform.compose(self.barb_incr)
        g = xform2.apply_to(self.base)
        offset = len(self.verts)
        self.verts.extend(g)

        # Connect parallel faces:
        n = len(self.base)
        for i, b0 in enumerate(bound):
            j = (i + 1) % n
            b1 = bound[j]
            a0 = offset + i
            a1 = offset + j
            self.faces.append([a0, a1, b1, b0])

        self.barb(iters-1, xform2, [offset, offset + 1, offset + 2, offset + 3])
