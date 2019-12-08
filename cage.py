import itertools

import meshutil
import stl.mesh
import numpy

class Cage(object):
    """An ordered list of polygons (or polytopes, technically)."""
    def __init__(self, verts, splits):
        # Element i of 'self.splits' gives the row index in 'self.verts'
        # in which polygon i begins.
        self.splits = splits
        # NumPy array of shape (N,3)
        self.verts = verts
    @classmethod
    def from_arrays(cls, *arrs):
        """
        Pass any number of array-like objects, with each one being a
        nested array with 3 elements - e.g. [[0,0,0], [1,1,1], [2,2,2]] -
        providing points.
        Each array-like object is treated as vertices describing a
        polygon/polytope.
        """
        n = 0
        splits = [0]*len(arrs)
        for i,arr in enumerate(arrs):
            splits[i] = n
            n += len(arr)
        verts = numpy.zeros((n,3), dtype=numpy.float64)
        # Populate it accordingly:
        i0 = 0
        for arr in arrs:
            i1 = i0 + len(arr)
            verts[i0:i1, :] = arr
            i0 = i1
        return cls(verts, splits)
    def polys(self):
        """Return iterable of polygons as (views of) NumPy arrays."""
        count = len(self.splits)
        for i,n0 in enumerate(self.splits):
            if i+1 < count:
                n1 = self.splits[i+1]
                yield self.verts[n0:n1,:]
            else:
                yield self.verts[n0:,:]
    def subdivide_deprecated(self):
        # assume self.verts has shape (4,3).
        # Midpoints of every segment:
        mids = (self.verts + numpy.roll(self.verts, -1, axis=0)) / 2
        # Centroid:
        centroid = numpy.mean(self.verts, axis=0)
        # Now, every single new boundary has: one vertex of 'bound', an
        # adjacent midpoint, a centroid, and the other adjacent midpoint.
        arrs = [
                [self.verts[0,:], mids[0,:],       centroid,        mids[3,:]],
                [mids[0,:],       self.verts[1,:], mids[1,:],       centroid],
                [centroid,        mids[1,:],       self.verts[2,:], mids[2,:]],
                [mids[3,:],       centroid,        mids[2,:],       self.verts[3,:]],
        ]
        # The above respects winding order and should not add any rotation.
        # I'm sure it has a pattern I can factor out, but I've not tried
        # yet.
        cages = [Cage(numpy.array(a), self.splits) for a in arrs]
        return cages
    def is_fork(self):
        return False
    def transform(self, xform):
        """Apply a Transform to all vertices, returning a new Cage."""
        return Cage(xform.apply_to(self.verts), self.splits)

class CageFork(object):
    """A series of generators that all split off in such a way that their
    initial polygons collectively cover all of some larger polygon, with
    no overlap.  The individual generators must produce either Cage, or
    more CageFork.
    """
    def __init__(self, gens):
        self.gens = gens
    def is_fork(self):
        return True

class CageGen(object):
    """A generator, finite or infinite, that produces objects of type Cage.
    It can also produce CageFork, but only a single one as the final value
    of a finite generator."""
    def __init__(self, gen):
        self.gen = gen
    def to_mesh(self, count=None, flip_order=False, loop=False, close_first=False,
                close_last=False, join_fn=meshutil.join_boundary_simple):
        #print("to_mesh(count={})".format(count))
        # Get 'opening' polygons of generator:
        cage_first = next(self.gen)
        # TODO: Avoid 'next' here so that we can use a list, not solely a
        # generator/iterator.
        if cage_first.is_fork():
            # TODO: Can it be a fork? Does that make sense?
            raise Exception("First element in CageGen can't be a fork.")
        cage_last = cage_first
        meshes = []
        # Close off the first polygon if necessary:
        if close_first:
            for poly in cage_first.polys():
                meshes.append(meshutil.close_boundary_simple(poly))
        # Generate all polygons from there and connect them:
        #print(self.gen)
        for i, cage_cur in enumerate(self.gen):
            #print("{}: {}".format(i, cage_cur))
            if count is not None and i >= count:
                # We stop recursing here, so close things off if needed:
                if close_last:
                    for poly in cage_last.polys():
                        meshes.append(meshutil.close_boundary_simple(poly))
                break
            # If it's a fork, then recursively generate all the geometry
            # from them, depth-first:
            if cage_cur.is_fork():
                # TODO: Clean up these recursive calls; parameters are ugly.
                # Some of them also make no sense in certain combinations
                # (e.g. loop with fork)
                for gen in cage_cur.gens:
                    m = gen.to_mesh(count=count - i, flip_order=flip_order, loop=loop,
                                    close_first=False, close_last=False,
                                    join_fn=join_fn)
                    # TODO: How do I handle closing with CageFork?
                    meshes.append(m)
                # A fork can be only the final element, so disregard anything
                # after one and just quit:
                break
            if flip_order:
                for b0,b1 in zip(cage_cur.polys(), cage_last.polys()):
                    m = join_fn(b0, b1)
                    meshes.append(m)
            else:
                for b0,b1 in zip(cage_cur.polys(), cage_last.polys()):
                    m = join_fn(b1, b0)
                    meshes.append(m)
            cage_last = cage_cur
        if loop:
            for b0,b1 in zip(cage_last.polys(), cage_first.polys()):
                if flip_order:
                    m = join_fn(b1, b0)
                else:
                    m = join_fn(b0, b1)
                meshes.append(m)
        # TODO: close_last?
        # or should this just look for whether or not the
        # generator ends here (without a CageFork)?
        mesh = meshutil.FaceVertexMesh.concat_many(meshes)
        return mesh
