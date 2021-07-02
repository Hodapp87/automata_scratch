# 2021-06-28, Chris Hodapp
import numpy as np

# Run this in Blender.  See something like loader.py.

# This is a royal clusterfucked jumble *but* it generates a cube
# something like the first stage of a Menger sponge.  There is a lot
# of extra work being done here.

# Known bugs:
# - Doesn't set the crease properly always?
# - I need to properly denote which faces *don't* need built
# (but I still need to run most code paths on all faces because
# of the structures they build up)
# - I handle only the main 4 vertices and no others

# Adjust 'f' to set the size of the central hole. (f=1/3 is 'normal')
#f = 1/4
def cube_thing(vert_accum, face_accum, base_idxs, vert_between=None, f=1/4):
    xform = lambda v: v + np.array([2.0, 0.0, 0.0])
    v0,v1,v2,v3 = base_idxs
    v4 = len(vert_accum)
    v5 = v4+1
    v6 = v5+1
    v7 = v6+1
    vert_accum.extend([xform(vert_accum[i]) for i in base_idxs])
    faces = [
        (v0,v1,v2,v3),
        (v4,v5,v1,v0),
        (v5,v6,v2,v1),
        (v7,v6,v5,v4),
        (v3,v2,v6,v7),
        (v0,v3,v7,v4),
    ]
    # key = vertex, value = list of adjacent faces (counter-clockwise)
    vert_to_faces = {
        v0: [5,1,0],
        v1: [1,2,0],
        v2: [0,2,4],
        v3: [0,4,5],
        v4: [3,1,5],
        v5: [2,1,3],
        v6: [4,2,3],
        v7: [4,3,5],
    }
    
    # key = (vert idx 1, vert idx 2).
    # value = index of vertex factor 'f' between 1 & 2.
    # (key is *not* symmetrical!)
    if vert_between is None:
        vert_between = {}
    # faces_inner_vertex[i] will have the corresponding face-split vertices
    # nearest to the vertices in faces[i]
    face_inner_vertex = [None for _ in faces]
    for f_idx, vert_idxs in enumerate(faces):
        n = len(vert_idxs)
        face_inner_vertex[f_idx] = [None]*len(vert_idxs)
        # Split each edge:
        print(f"{vert_idxs}:")
        for i, v in enumerate(vert_idxs):
            # v = 'current' vertex index.
            # vp = 'previous' vertex, vn = 'next' vertex:
            vp = vert_idxs[(i + n - 1) % n]
            vn = vert_idxs[(i + 1) % n]
            coord_v = vert_accum[v]
            coord_vp = vert_accum[vp]
            coord_vn = vert_accum[vn]
            print(f"{v}:{coord_v} {vp}:{coord_vp} {vn}:{coord_vn}")
            # Go f of way from v to vn:
            if (v,vn) not in vert_between:
                coord_vnf = (1-f)*coord_v + f*coord_vn
                vert_between[(v, vn)] = len(vert_accum)
                vert_accum.append(coord_vnf)
            # and from v to vp:
            if (v,vp) not in vert_between:
                coord_vpf = (1-f)*coord_v + f*coord_vp
                vert_between[(v, vp)] = len(vert_accum)
                vert_accum.append(coord_vpf)
        # Now, go 'across' those new edge splits too.
        # In particular, if starting at vertex i, and vertex j is next,
        # then join between:
        # - i's split to its *previous* vertex
        # - j's split to its *next* vertex
        for i, vi in enumerate(vert_idxs):
            j = (i + 1) % n
            vj = vert_idxs[j]
            vi_prev = vert_idxs[(i + n - 1) % n]
            vj_next = vert_idxs[(j + 1) % n]
            vi_split = vert_between[(vi, vi_prev)]
            vj_split = vert_between[(vj, vj_next)]
            coord = (1-f)*vert_accum[vi_split] + f*vert_accum[vj_split]
            # vb = our new vertex between vi_split & vj_split:
            vb = len(vert_accum)
            vert_between[(vi_split, vj_split)] = vb
            face_inner_vertex[f_idx][i] = vb
            vert_accum.append(coord)
            # note that this is also between two others:
            vert_between[(vert_between[(vi,vj)], vert_between[(vi_prev,vj_next)])] = vb
            # As we do this, make corner faces, because we know the vertices:
            face_accum.append((vi, vert_between[(vi, vj)], vb, vi_split))
        # and make faces between those:
        for i, vi in enumerate(vert_idxs):
            vi_next = vert_idxs[(i + 1) % n]
            vi_prev = vert_idxs[(i + n - 1) % n]
            vi_prev2 = vert_idxs[(i + n - 2) % n]
            vi_split = vert_between[(vi, vi_next)]
            vi_split2 = vert_between[(vi_prev, vi_prev2)]
            vb_i = vert_between[(vi_split, vi_split2)]
            vb_i2 = vert_between[(vi_split2, vi_split)]
            face_accum.append((
                vert_between[(vi, vi_prev)],
                vb_i,
                vb_i2,
                vert_between[(vi_prev, vi)],
            ))

    # key = corner vertex index, value = nearest 'inside' corner vertex
    # (i.e. of the 8 'inside' vertices, the nearest to this corner -
    # always diagonally away through the cube's interior)
    vertex_to_inner = {}

    # face_idx_opp[i] gives the face that is *opposite* face i
    face_idx_opp = [None for _ in faces]
    # face_remap_opp[i] gives the vertices for face_idx_opp[i] -
    # as indices into faces[face_idx_opp[i]], and in an order that moves
    # in lockstep with faces[i], i.e. opposite winding order and always with
    # 'opposite' vertices at the same index.
    face_remap_opp = [None for _ in faces]

    # TODO: Feels a little wrong to hard-code?
    for vi in range(8):
        v = list(vert_to_faces.keys())[vi]
        # f_inc = all faces incident on corner v
        f_inc = vert_to_faces[v]
        for i,f0_idx in enumerate(f_inc):
            # Look at the *other* two incident faces:
            f1_idx = f_inc[(i + 1) % 3]
            f2_idx = f_inc[(i - 1) % 3]
            f1 = faces[f1_idx]
            f2 = faces[f2_idx]
            # Find v in both these faces:
            v_idx1 = f1.index(v)
            v_idx2 = f2.index(v)
            # We want the 'opposite' vertex: one adjacent to v, but not in face f0.
            # It's adjacent to v in both f1 and f2, so choices are limited.
            v1p = f1[(v_idx1 - 1) % len(f1)]
            v1n = f1[(v_idx1 + 1) % len(f1)]
            v2p = f2[(v_idx2 - 1) % len(f2)]
            v2n = f2[(v_idx2 + 1) % len(f2)]
            for v1 in (v1p, v1n):
                for v2 in (v2p, v2n):
                    if v1 == v2:
                        v_opp = v1
            # Find the 'opposite' face to f0 too. (v_opp is incident on it,
            # but it's the only face that isn't f1 or f2).
            f_inc2 = vert_to_faces[v_opp]
            for f_try in f_inc2:
                if f_try == f1_idx or f_try == f2_idx:
                    continue
                f_opp_idx = f_try
            face_idx_opp[f0_idx] = f_opp_idx
            face_idx_opp[f_opp_idx] = f0_idx
            # Since they are *opposite* faces but they have consistent winding order,
            # if we start at corresponding vertices (i.e. v and v_opp) and walk in
            # *opposite* directions, we will walk to corresponding vertices.
            f0 = faces[f0_idx]
            f_opp = faces[f_opp_idx]
            n = len(f0)
            v_idx = f0.index(v)
            v_opp_idx = f_opp.index(v_opp)
            face_remap_opp[f0_idx] = [(v_opp_idx + v_idx - j) % n for j in range(n)]

    # I don't even know... mark out the redundant ways of reaching the
    # same 8 inner vertices.
    for vi in range(8):
        v = list(vert_to_faces.keys())[vi]
        # f_inc = all faces incident on corner v
        f_inc = vert_to_faces[v]
        for k,f0_idx in enumerate(f_inc):
            # Again, for some face incident on v, find the opposite face and
            # walk around its corresponding opposite vertices.
            f0 = faces[f0_idx]
            f_opp_idx = face_idx_opp[f0_idx]
            remap = face_remap_opp[f0_idx]
            f_opp = [faces[f_opp_idx][j] for j in remap]
            # That is, f0[i] and f_opp[i] are opposite vertices (they have one
            # edge between them and sit on opposite faces).
            print(f"face {f0_idx}: {f0} opposite {f_opp}")
            # Now, translate this to their corresponding nearest face-split vertices
            # on their respective faces.
            f0_split = face_inner_vertex[f0_idx]
            f_opp_split = [face_inner_vertex[f_opp_idx][j] for j in remap]
            print(f"face {f0_idx} inner: {f0_split} opposite {f_opp_split}")
            # Make 'inner' vertices nearest f0_split & f_opp_split:
            for i,(m,n) in enumerate(zip(f0_split, f_opp_split)):
                equiv = [(m,n)]
                # Find 'neighbor' faces to the i'th vertex:
                for f1_idx in vert_to_faces[f0[i]]:
                    if f1_idx == f0_idx:
                        # Ignore the same face.
                        continue
                    f1_opp_idx = face_idx_opp[f1_idx]
                    print(f"f0_idx={f0_idx}, f0[i]={f0[i]}, f1_idx={f1_idx} opposite={f1_opp_idx}")
                    # Find f0[i] in that neighbor face f1...
                    f1_v_idx = faces[f1_idx].index(f0[i])
                    # ...so we can find this neighbor face's face-split vertex
                    # that is nearest v:
                    v_f1_split = face_inner_vertex[f1_idx][f1_v_idx]
                    # and then find the vertex across from that:
                    remap2 = face_remap_opp[f1_idx][f1_v_idx]
                    v_opp_split = face_inner_vertex[f1_opp_idx][remap2]
                    print(f"    nearest split vertex: {v_f1_split}, opp {v_opp_split}")
                    equiv.append((v_f1_split, v_opp_split))
                found = None
                for m2,n2 in equiv:
                    if (m2,n2) in vert_between:
                        found = vert_between[(m2,n2)]
                        break
                if found is None:
                    vert = (1-f)*vert_accum[m] + f*vert_accum[n]
                    found = len(vert_accum)
                    vert_accum.append(vert)
                for m2,n2 in equiv:
                    vert_between[(m2,n2)] = found
                print(f"equivalent between verts {m},{n}: {equiv}")

    # Pick a vertex:
    vi = 3
    v = list(vert_to_faces.keys())[vi]
    f_inc = vert_to_faces[v]

    for k,f0_idx in enumerate(f_inc):
        # Again, for some face incident on v, find the opposite face and
        # walk around its corresponding opposite vertices.
        f0 = faces[f0_idx]
        f_opp_idx = face_idx_opp[f0_idx]
        remap = face_remap_opp[f0_idx]
        f_opp = [faces[f_opp_idx][j] for j in remap]
        # That is, f0[i] and f_opp[i] are opposite vertices (they have one
        # edge between them and sit on opposite faces).
        # Now, translate this to their corresponding nearest face-split vertices
        # on their respective faces.
        f0_split = face_inner_vertex[f0_idx]
        f_opp_split = [face_inner_vertex[f_opp_idx][j] for j in remap]
        for i,_ in enumerate(f0):
            j = (i + 1) % len(f0)
            face_accum.append((
                f0_split[i],
                f0_split[j],
                vert_between[(f0_split[j], f_opp_split[j])],
                vert_between[(f0_split[i], f_opp_split[i])],
            ))
            face_accum.append((
                f_opp_split[j],
                f_opp_split[i],
                vert_between[(f_opp_split[i], f0_split[i])],
                vert_between[(f_opp_split[j], f0_split[j])],
            ))
    return vert_accum, face_accum, (v4,v5,v6,v7), vert_between

base_verts = [
    (-1, -1, -1),
    (-1, -1,  1),
    (-1,  1,  1),
    (-1,  1, -1),
]
base_verts = [np.array(t) for t in base_verts]

def cube_iterate(count=4):
    f = []
    btw = {}
    v = base_verts.copy()
    idxs = [i for i,_ in enumerate(base_verts)]
    for i in range(count):
        print(i)
        v,f,idxs,btw = cube_thing(v, f, idxs, btw)
    v = [tuple(i) for i in v]
    return v,f
