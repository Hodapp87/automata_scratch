To-do items, wanted features, bugs:

- Examples of branching. This will probably need recursion via functions
  (or an explicit stack some other way).
- I need to figure out winding order.  It is consistent through seemingly
  everything, except for reflection and close_boundary_simple.
  (When there are two parallel boundaries joined with something like
  join_boundary_simple, traversing these boundaries in their actual order
  to generate triangles - like in close_boundary_simple - will produce
  opposite winding order on each. Imagine a transparent clock: seen from the
  front, it moves clockwise, but seen from the back, it moves
  counter-clockwise.)
- Make it easier to build up meshes a bit at a time?
- Factor out recursive/iterative stuff to be a bit more concise
- Embed this in Blender?
- File that bug that I've seen in trimesh/three.js
  (see trimesh_fail.ipynb)
  
- Parametrize gen_twisted_boundary over boundaries and
do my nested spiral
- Encode the notions of "generator which transforms an
existing list of boundaries", "generator which transforms
another generator"
- This has a lot of functions parametrized over a lot
of functions.  Need to work with this somehow.
- Work directly with lists of boundaries. The only thing
I ever do with them is apply transforms to all of them, or
join adjacent ones with corresponding elements.
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
- I need an actual example of branching/forking. If I simply
split a boundary into sub-boundaries per the rules I already
have in my notes, then this still lets me split any way I want
to without having to worry about joining N boundaries instead
of 2, doesn't it?

Other notes:
- Picking at random the diagonal on the quad to triangulate with
  does seem to turn 'error' just to noise, and in its own way this
  is preferable.
