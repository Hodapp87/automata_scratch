# To-do items, wanted features, bugs:

## Cool
- More complicated: Examples of *merging*. I'm not sure on the theory
  behind this.
  
## Annoying/boring
- https://en.wikipedia.org/wiki/Polygon_triangulation - do this to
  fix my wave example!
  - http://www.polygontriangulation.com/2018/07/triangulation-algorithm.html
- Clean up examples.ram_horn_branch(). The way I clean it up might
  help inform some cleaner designs.
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
- Integrate parallel_transport work and reuse what I can
- /mnt/dev/graphics_misc/isosurfaces_2018_2019 - perhaps include my
  spiral isosurface stuff from here

## Abstractions

- This has a lot of functions parametrized over a lot
  of functions.  Need to work with this somehow.  (e.g. should
  it subdivide this boundary? should it merge opening/closing
  boundaries?)
- Some generators produce boundaries that can be directly merged
  and produce sensible geometry.  Some generators produce
  boundaries that are only usable when they are further
  transformed (and would produce degenerate geometry).  What sort
  of nomenclature captures this?

- How can I capture the idea of a group of parameters which, if
  they are all scaled in the correct way (some linearly, others
  inversely perhaps), generated geometry that is more or less
  identical except that it is higher-resolution?
- Use mixins to extend 3D transformations to things (matrices,
  cages, meshes, existing transformations)
- I can transform a Cage.  Why not a CageGen?
  
## ????
- Embed this in Blender?
  
## Future thoughts

- What if I had a function that could generate a Cage as if
  from a parametric formula and smoothly vary its orientation?
  My existing tools could easily turn this to a mesh. If I could vary
  the detail of the Cage itself (if needed), then I could also
  generate a mesh at an arbitrary level of detail simply by sampling at
  finer and finer points on the parameter space.  (This might also tie
  into the Parallel Transport work.)
- What are the limitations of using Cages?
- Current system is very "generative".  Could I do basically L-system
  if I have rules for how a much is *refined*?  What about IFS?
- Do this in Rust once I understand WTF I am doing

## Other thoughts

- Why do I never use the term "extruding" to describe what I'm doing?