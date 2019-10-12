# To-do items, wanted features, bugs:

## Cool
- Examples of branching. This will probably need recursion via functions
  (or an explicit stack some other way).  If I simply
  split a boundary into sub-boundaries per the rules I already
  have in my notes, then this still lets me split any way I want
  to without having to worry about joining N boundaries instead
  of 2, doesn't it?
  - Note that for this to work right, either gen2mesh has to be
    called separately on every straight portion, or I have to
    make a version of gen2mesh that can handle something more
    like trees of boundaries, not just flat lists.
- More complicated: Examples of *merging*. I'm not sure on the theory
  behind this.
  
## Annoying
- I really need to standardize some of the behavior of fundamental
  operations (with regard to things like sizes they generate). This
  is behavior that, if it changes, will change a lot of things that I'm
  trying to keep consistent so that my examples still work.
- Winding order.  It is consistent through seemingly
  everything, except for reflection and close_boundary_simple.
  (When there are two parallel boundaries joined with something like
  join_boundary_simple, traversing these boundaries in their actual order
  to generate triangles - like in close_boundary_simple - will produce
  opposite winding order on each. Imagine a transparent clock: seen from the
  front, it moves clockwise, but seen from the back, it moves
  counter-clockwise.)
- File that bug that I've seen in trimesh/three.js
  (see trimesh_fail.ipynb)
- Why do I get the weird zig-zag pattern on the triangles,
  despite larger numbers of them? Is it something in how I
  twist the frames?
  - How can I compute the *torsion* on a quad? I think it
    comes down to this: torsion applied across the quad I'm
    triangulating leading to neither diagonal being a
    particularly good choice.  Subdividing the boundary seems
    to help, but other triangulation methods (e.g. turning a
    quad to 4 triangles by adding the centroid) could be good
    too.
  - Facets/edges are just oriented the wrong way...
  - Picking at random the diagonal on the quad to triangulate with
    does seem to turn 'error' just to noise, and in its own way this
    is preferable.

## Abstractions

- Encode the notions of "generator which transforms an
  existing list of boundaries", "generator which transforms
  another generator"
- This has a lot of functions parametrized over a lot
  of functions.  Need to work with this somehow.  (e.g. should
  it subdivide this boundary? should it merge opening/closing
  boundaries?)
- Work directly with lists of boundaries. The only thing
  I ever do with them is apply transforms to all of them, or
  join adjacent ones with corresponding elements.

- Some generators produce boundaries that can be directly merged
  and produce sensible geometry.  Some generators produce
  boundaries that are only usable when they are further
  transformed (and would produce degenerate geometry).  What sort
  of nomenclature captures this?

- How can I capture the idea of a group of parameters which, if
  they are all scaled in the correct way (some linearly, others
  inversely perhaps), generated geometry that is more or less
  identical except that it is higher-resolution?
## ????
- Embed this in Blender?
  
