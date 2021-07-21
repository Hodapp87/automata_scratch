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
        trans_verts = numpy.zeros((2*len(self.verts),3), dtype=self.verts.dtype)
        for i,(v,m) in enumerate(zip(self.verts, mids)):
            trans_verts[2*i] = v
            trans_verts[2*i+1] = m
        trans_edges = [[7, 0, 1], [1, 2, 3], [3, 4, 5], [5, 6, 7]]
        return cages, trans_verts, trans_edges
    def subdivide_x_deprecated(self):
        mids = (self.verts + numpy.roll(self.verts, -1, axis=0)) / 2
        centroid = numpy.mean(self.verts, axis=0)
        arrs = [
                [self.verts[0,:], mids[0,:],       mids[2,:],       self.verts[3,:]],
                [mids[0,:],       self.verts[1,:], self.verts[2,:], mids[2,:]],
        ]
        cages = [Cage(numpy.array(a), self.splits) for a in arrs]
        trans_verts = numpy.zeros((2*len(self.verts),3), dtype=self.verts.dtype)
        for i,(v,m) in enumerate(zip(self.verts, mids)):
            trans_verts[2*i] = v
            trans_verts[2*i+1] = m
        trans_edges = [[7, 0, 1], [1, 2, 3], [3, 4, 5], [5, 6, 7]]
        return cages, trans_verts, trans_edges
    def is_fork(self):
        return False
    def transform(self, xform):
        """Apply a Transform to all vertices, returning a new Cage."""
        return Cage(xform.apply_to(self.verts), self.splits)
    def classify_overlap(self, cages):
        """Classifies each vertex in a list of cages according to some rules.
        
        (This is mostly used in order to verify that certain rules are
        followed when a mesh is undergoing forking/branching.)
        
        Returns:
        v -- List of length len(cages).  v[i] is a numpy array of shape (N,)
        where N is the number of vertices in cages[i] (i.e. rows of
        cages[i].verts).  Element v[i][j] gives a classification of
        X=l[i].verts[j] that will take values below:
        
        0 -- None of the below apply to X.
        1 -- X lies on an edge in this Cage (i.e. self).
        2 -- X equals another (different) vertex somewhere in 'cages', and
             case 1 does not apply.
        3 -- X equals a vertex in self.verts.
        """
        v = [numpy.zeros((cage.verts.shape[0],), dtype=numpy.uint8)
             for cage in cages]
        # for cage i of all the cages...
        for i, cage in enumerate(cages):
            # for vertex j within cage i...
            for j, vert in enumerate(cage.verts):
                # Check against every vert in our own (self.verts):
                for vert2 in self.verts:
                    if numpy.allclose(vert, vert2):
                        v[i][j] = 3
                        break
                if v[i][j] > 0:
                    continue
                # Check against every edge of our own polygons:
                for poly in self.polys():
                    for k,_ in enumerate(poly):
                        # Below is because 'poly' is cyclic (last vertex
                        # has an edge to the first):
                        k2 = (k + 1) % len(poly)
                        # Find distance from 'vert' to each vertex of the edge:
                        d1 = numpy.linalg.norm(poly[k,:] - vert)
                        d2 = numpy.linalg.norm(poly[k2,:] - vert)
                        # Find the edge's length:
                        d = numpy.linalg.norm(poly[k2,:] - poly[k,:])
                        # These are equal if and only if the vertex lies along
                        # that edge:
                        if numpy.isclose(d, d1 + d2):
                            v[i][j] = 1
                            break
                    if v[i][j] > 0:
                        break
                if v[i][j] > 0:
                    continue
                # Check against every *other* vert in cages:
                for i2, cage2 in enumerate(cages):
                    for j2, vert2 in enumerate(cage.verts):
                        if i == i2 and j == j2:
                            # same cage, same vertex - ignore:
                            continue
                        if numpy.allclose(vert, vert2):
                            v[i][j] = 2
                            break
                    if v[i][j] > 0:
                        break
        return v

class CageFork(object):
    """A series of generators that all split off in such a way that their
    initial polygons collectively cover all of some larger polygon, with
    no overlap.  The individual generators must produce either Cage, or
    more CageFork.
    
    Transition vertices and edges are here to help adapt this CageFork
    to an earlier Cage, which may require subdividing its edges.
    
    Vertices (in 'verts') should proceed in the same direction around the
    cage, and start at the same vertex.  Edges (in 'edges') should have N
    elements, one for each of N vertices in the 'starting' Cage (the one
    that we must adapt *from*), and edges[i] should itself be a list in
    which each element is a (row) index of 'verts'.  edges[i] specifies,
    in correct order, which vertices in 'verts' should connect to vertex
    i of the 'starting' Cage.  In its entirety, it also gives the
    'transition' Cage (hence, order matters in the inner lists).
    
    As an example, if a starting cage is [0, 0, 0], [1, 0, 0], [1, 1, 0],
    [0, 1, 0] and the CageFork simply subdivides into 4 equal-size cages,
    then 'verts' might be [[0, 0, 0], [0.5, 0, 0], [1, 0, 0], [1, 0.5, 0],
    [1, 1, 0], [0.5, 1, 0], [0, 1, 0], [0, 0.5, 0]] - note that it begins
    at the same vertex, subdivides each edge, and (including the cyclic
    nature) ends at the same vertex.  'edges' then would be:
    [[7, 0, 1], [1, 2, 3], [3, 4, 5], [5, 6, 7]].  Note that every vertex
    in the starting cage connects to 3 vertices in 'verts' and overlaps
    with the previous and next vertex.
    
    (Sorry. This is explained badly and I know it.)
    
    Parameters:
    gens -- explained above
    verts -- Numpy array with 'transition' vertices, shape (M,3)
    edges -- List of 'transition' edges
    """
    def __init__(self, gens, verts, edges):
        self.gens = gens
        self.verts = verts
        self.edges = edges
    def is_fork(self):
        return True
    def transition_from(self, cage):
        """Generate a transitional mesh to adapt the given starting Cage"""
        #print("DEBUG: Transition from {} to {}".format(cage.verts, self.verts))
        vs = numpy.concatenate([cage.verts, self.verts])
        # Indices 0...offset-1 are from cage, rest are from self.verts
        offset = cage.verts.shape[0]
        # We have one face for total sub-elements in self.edges:
        count = sum([len(e) for e in self.edges])
        fs = numpy.zeros((count, 3), dtype=int)
        face_idx = 0
        for j, adjs in enumerate(self.edges):
            for k, adj in enumerate(adjs[:-1]):
                adj_next = adjs[(k + 1) % len(adjs)]
                # Proceed in direction of cage.verts:
                fs[face_idx] = [j, offset + adj_next, offset + adj]
                face_idx += 1
            fs[face_idx] = [j, (j + 1) % len(cage.verts), offset + adjs[-1]]
            face_idx += 1
        return meshutil.FaceVertexMesh(vs, fs)

class CageGen(object):
    """A generator, finite or infinite, that produces objects of type Cage.
    It can also produce CageFork, but only a single one as the final value
    of a finite generator."""
    def __init__(self, gen):
        self.gen = gen
    def to_mesh(self, count=None, flip_order=False, loop=False, close_first=False,
                close_last=False, join_fn=meshutil.join_boundary_simple):
        # Get 'opening' polygons of generator:
        cage_first = next(self.gen)
        #print("DEBUG: to_mesh(count={}), cage_first={}".format(count, cage_first.verts))
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
            #print("DEBUG: i={}, cage_cur={}, cage_last={}".format(i, cage_cur, cage_last.verts))
            #print("{}: {}".format(i, cage_cur))
            if count is not None and i >= count:
                # We stop recursing here, so close things off if needed:
                if close_last:
                    for poly in cage_last.polys():
                        meshes.append(meshutil.close_boundary_simple(poly, reverse=True))
                    # TODO: Fix the winding order hack here.
                break
            # If it's a fork, then recursively generate all the geometry
            # from them, depth-first:
            if cage_cur.is_fork():
                # First, transition the cage properly:
                mesh_trans = cage_cur.transition_from(cage_last)
                meshes.append(mesh_trans)
                # TODO: Clean up these recursive calls; parameters are ugly.
                # Some of them also make no sense in certain combinations
                # (e.g. loop with fork)
                for gen in cage_cur.gens:
                    m = gen.to_mesh(count=count - i, flip_order=flip_order, loop=loop,
                                    close_first=False, close_last=close_last,
                                    join_fn=join_fn)
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
        mesh = meshutil.FaceVertexMesh.concat_many(meshes)
        return mesh
